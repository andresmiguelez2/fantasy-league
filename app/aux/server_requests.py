from fastapi import FastAPI
from pydantic import BaseModel
import logging
import psycopg2
import os


logger = logging.getLogger(__name__)

server_app = FastAPI()


@server_app.get("/ping")
def ping():
    return {"status": "ok", "message": "pong"}


@server_app.get("/squads/{player_id}")
def squad(player_id: int):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres_db"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432"),
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM footballer WHERE owner_id = %s ORDER BY id
            """,
            (player_id,),
        )
        players = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"players": players}
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {"players": []}
    

@server_app.get("/market")
def market():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres_db"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432"),
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM footballer
            WHERE on_market = TRUE
            ORDER BY owner_id, on_market_since 
            """
        )
        players = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"players": players}
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {"players": []}


class BidRequest(BaseModel):
    player_id: int
    footballer_id: int
    bid_amount: int

@server_app.post("/market/bids")
def place_bid(bid: BidRequest):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres_db"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432"),
        )
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bid (footballer_id, bidder_id, amount, timestamp)
            VALUES (%s, %s, %s, now())
            """,
            (bid.footballer_id, bid.player_id, bid.bid_amount)
        )
        logger.info(f"Received bid: Player {bid.player_id} bids {bid.bid_amount} on tootballer {bid.footballer_id}")
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": "Bid placed successfully."}
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {"status": "error", "message": str(e)}


