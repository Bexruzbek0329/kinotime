"""FastAPI admin API entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from admin.api.routes import auth, movies, users, channels, settings_router, stats, broadcast, admins, logs
import structlog
import asyncio
import os
from main_bot import main as run_bot

log = structlog.get_logger()

_bot_task: asyncio.Task | None = None
_bot_status: str = "not_started"
_bot_error: str | None = None


async def _safe_run_bot() -> None:
    """Supervised runner for the Telegram bot with auto-restart on unexpected crashes."""
    global _bot_status, _bot_error
    _bot_status = "starting"
    retry_delay = 5
    while True:
        try:
            log.info("bot_polling_task_started")
            _bot_status = "running"
            _bot_error = None
            await run_bot()
            _bot_status = "stopped"
            break
        except asyncio.CancelledError:
            _bot_status = "cancelled"
            log.info("bot_polling_task_cancelled")
            break
        except Exception as e:
            _bot_status = "crashed"
            _bot_error = f"{type(e).__name__}: {str(e)}"
            log.error("bot_background_task_crashed", error=str(e), exc_info=True)
            log.info("bot_restart_scheduled", delay_seconds=retry_delay)
            await asyncio.sleep(retry_delay)


async def _keep_alive_pinger() -> None:
    """Periodically ping public health endpoint through Alwaysdata proxy to keep upstream alive."""
    await asyncio.sleep(20)
    import httpx
    target_url = os.getenv("KEEP_ALIVE_URL", "https://kinobotuz.alwaysdata.net/api/health")
    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            try:
                r = await client.get(target_url)
                log.debug("keepalive_ping_sent", status=r.status_code)
            except Exception as e:
                log.debug("keepalive_ping_error", error=str(e))
            await asyncio.sleep(35)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bot_task, _bot_status
    log.info("api_starting")
    ping_task = None
    if os.getenv("RUN_BOT", "true").lower() in ("true", "1", "yes"):
        _bot_task = asyncio.create_task(_safe_run_bot())
        log.info("background_bot_task_launched")
    # Start self-pinging keepalive to prevent Alwaysdata from killing the process on idle
    ping_task = asyncio.create_task(_keep_alive_pinger())
    yield
    if ping_task:
        ping_task.cancel()
    if _bot_task:
        _bot_task.cancel()
        try:
            await _bot_task
        except (asyncio.CancelledError, Exception):
            pass
    _bot_status = "stopped"
    log.info("api_stopped")


app = FastAPI(
    title="KinoBot Admin API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"^https?:\/\/.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(movies.router, prefix="/api/movies", tags=["movies"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["settings"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(broadcast.router, prefix="/api/broadcast", tags=["broadcast"])
app.include_router(admins.router, prefix="/api/admins", tags=["admins"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "bot_status": _bot_status,
        "bot_error": _bot_error,
        "version": "2026.09.30-keepalive",
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("IP", "0.0.0.0")
    uvicorn.run("main_api:app", host=host, port=port)
