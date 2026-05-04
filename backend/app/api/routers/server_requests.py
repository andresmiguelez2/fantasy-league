import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from .logger import logger
from fastapi.middleware.cors import CORSMiddleware

# import sub-routers
from . import auth
from . import league
from . import market
from . import leaderboard
from . import footballer
from . import squad
from . import player
from . import general
from . import team


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Deferred import avoids a circular dependency: tasks.py imports from
    # server_requests modules, so importing it at module level here would
    # create a cycle.
    task = None
    background_tasks_enabled = os.getenv("ENABLE_BACKGROUND_TASKS", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if background_tasks_enabled:
        from backend.app.tasks import background_loop

        task = asyncio.create_task(background_loop())
    yield
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


server_app = FastAPI(lifespan=lifespan)


def _get_allowed_origins() -> list[str]:
    origins_from_env = os.getenv("CORS_ALLOW_ORIGINS", "")
    origins = [origin.strip() for origin in origins_from_env.split(",") if origin.strip()]

    if origins:
        return origins

    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://0.0.0.0:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://0.0.0.0:8080",
    ]

server_app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@server_app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}


server_app.include_router(auth.router)
server_app.include_router(league.router)
server_app.include_router(market.router)
server_app.include_router(leaderboard.router)
server_app.include_router(footballer.router)
server_app.include_router(squad.router)
server_app.include_router(player.router)
server_app.include_router(general.router)
server_app.include_router(team.router)
