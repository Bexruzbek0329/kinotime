"""FastAPI admin API entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from admin.api.routes import auth, movies, users, channels, settings_router, stats, broadcast, admins, logs
import structlog

log = structlog.get_logger()

import asyncio
import os
from main_bot import main as run_bot

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("api_starting")
    bot_task = None
    if os.getenv("RUN_BOT", "true").lower() in ("true", "1", "yes"):
        bot_task = asyncio.create_task(run_bot())
        log.info("background_bot_task_launched")
    yield
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except (asyncio.CancelledError, Exception):
            pass
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
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("IP", "0.0.0.0")
    uvicorn.run("main_api:app", host=host, port=port)

