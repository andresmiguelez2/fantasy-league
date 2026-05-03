import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from core.logging import logger
from fastapi.middleware.cors import CORSMiddleware

# import sub-routers
from .routes import auth
from .routes import leagues
from .routes import market
from .routes import leaderboard
from .routes import footballers
from .routes import squads
from .routes import players
from .routes import general
from .routes import teams


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Deferred import avoids a circular dependency: workers/background.py imports from
    # api/routes modules, so importing it at module level here would create a cycle.
    task = None
    background_tasks_enabled = os.getenv("ENABLE_BACKGROUND_TASKS", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if background_tasks_enabled:
        from workers.background import background_loop

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
server_app.include_router(leagues.router)
server_app.include_router(market.router)
server_app.include_router(leaderboard.router)
server_app.include_router(footballers.router)
server_app.include_router(squads.router)
server_app.include_router(players.router)
server_app.include_router(general.router)
server_app.include_router(teams.router)
