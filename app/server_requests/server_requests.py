from fastapi import FastAPI
from .logger import logger


server_app = FastAPI()


@server_app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}


server_app.include_router(market.router)
server_app.include_router(bids.router)
server_app.include_router(leaderboard.router)