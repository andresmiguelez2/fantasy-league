import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from .logger import logger
from fastapi.middleware.cors import CORSMiddleware

# import sub-routers
from ...server_requests import auth
from ...server_requests import league
from ...server_requests import market
from ...server_requests import leaderboard
from ...server_requests import footballer
from ...server_requests import squad
from ...server_requests import player
from ...server_requests import general
from ...server_requests import team


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

server_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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
