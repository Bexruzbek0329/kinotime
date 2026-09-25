"""
Kinolar olami Telegram bot — entry point.

Startup sequence
----------------
1. Initialise the database (create tables, seed default settings).
2. Connect to Redis and create the FSM storage.
3. Build the :class:`~aiogram.Bot` and :class:`~aiogram.Dispatcher`.
4. Register middlewares in dependency order.
5. Register handler routers.
6. Start long-polling.
"""
import asyncio
import logging

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from sqlalchemy import select

from config import settings
from database.engine import AsyncSessionLocal, engine
from database.models.base import Base
from database.models.setting import DEFAULT_SETTINGS
from database.repositories.setting_repo import SettingRepository
from bot.middlewares.db import DatabaseMiddleware
from bot.middlewares.rate_limit import RateLimitMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.middlewares.user import UserMiddleware
from bot.handlers import (
    errors,
    file_id_helper,
    inline_query,
    main_menu,
    movie,
    profile,
    search,
    serial,
    start,
    subscription,
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

log = structlog.get_logger()


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------


async def init_db() -> None:
    """
    Create all tables (idempotent) and seed default settings rows that do
    not yet exist in the database.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        repo = SettingRepository(session)
        for key, value in DEFAULT_SETTINGS.items():
            existing = await repo.get(key)
            if existing is None:
                await repo.set(key, value)
        # Ensure at least one superadmin exists for admin panel access
        from database.models.admin import Admin, AdminRole
        import bcrypt
        admin_res = await session.execute(select(Admin).limit(1))
        if not admin_res.scalar_one_or_none():
            salt = bcrypt.gensalt()
            pwd_hash = bcrypt.hashpw(b"admin123", salt).decode("utf-8")
            default_admin = Admin(
                username="admin",
                password_hash=pwd_hash,
                role=AdminRole.superadmin,
                is_active=True,
            )
            session.add(default_admin)
            await session.commit()
            log.info("default_superadmin_seeded", username="admin")

    log.info("database_initialized")


# ---------------------------------------------------------------------------
# Main coroutine
# ---------------------------------------------------------------------------


async def main() -> None:
    """Assemble and run the bot."""
    await init_db()

    # Redis connection — optional with in-memory fallback
    redis = None
    storage = None
    try:
        r = Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        await asyncio.wait_for(r.ping(), timeout=2.0)
        redis = r
        storage = RedisStorage(redis=redis)
        log.info("redis_connected")
    except Exception as e:
        log.warning("redis_unavailable_fallback_to_memory", error=str(e))
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()


    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher(storage=storage)

    # Sync bot descriptions from database to Telegram
    try:
        async with AsyncSessionLocal() as session:
            repo = SettingRepository(session)
            bot_desc = await repo.get("bot_description")
            if bot_desc:
                await bot.set_my_description(description=bot_desc.strip()[:512])
            bot_short = await repo.get("bot_short_description")
            if bot_short:
                await bot.set_my_short_description(short_description=bot_short.strip()[:120])
        log.info("bot_descriptions_synced_on_startup")
    except Exception as e:
        log.warning("bot_descriptions_sync_failed_on_startup", error=str(e))

    # ------------------------------------------------------------------
    # Middlewares — order matters:
    # DatabaseMiddleware must run first so the session is available to all
    # downstream middlewares and handlers.
    # ------------------------------------------------------------------
    for observer in (dp.message, dp.callback_query):
        observer.middleware(DatabaseMiddleware())
        observer.middleware(UserMiddleware())

    dp.inline_query.middleware(DatabaseMiddleware())

    # Rate limiter on messages only (callbacks are naturally throttled by UX)
    dp.message.middleware(RateLimitMiddleware(redis))

    # Subscription gate on both messages and callbacks
    for observer in (dp.message, dp.callback_query):
        observer.middleware(SubscriptionMiddleware())

    # ------------------------------------------------------------------
    # Routers — errors router must be first so it can catch everything
    # ------------------------------------------------------------------
    dp.include_router(file_id_helper.router)  # Admin file_id helper — must be first
    dp.include_router(errors.router)
    dp.include_router(start.router)
    dp.include_router(subscription.router)
    dp.include_router(main_menu.router)
    dp.include_router(serial.router)
    dp.include_router(profile.router)
    dp.include_router(movie.router)
    dp.include_router(search.router)
    dp.include_router(inline_query.router)

    log.info("bot_starting", username=settings.bot_username)

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            handle_signals=False,
        )
    finally:
        await bot.session.close()
        if redis is not None:
            await redis.aclose()
        log.info("bot_stopped")



# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())
