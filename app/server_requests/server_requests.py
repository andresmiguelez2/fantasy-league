import asyncio
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
    from tasks import background_loop
    task = asyncio.create_task(background_loop())
    yield
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
