from fastapi import FastAPI
from .logger import logger
from fastapi.middleware.cors import CORSMiddleware


server_app = FastAPI()

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


server_app.include_router(market.router)
server_app.include_router(bids.router)
server_app.include_router(leaderboard.router)


