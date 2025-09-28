from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
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
    """Get the squad of a player."""
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
    """Get all players currently on the market."""
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
    

@server_app.get("/market/{player_id}")
def player_market(player_id: int):
    """Get all players currently on the market with bid info for a specific player.
    
    Args:
        player_id (int): The ID of the player to get bid info for."""
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
            SELECT 
                f.id
                , f.name
                , f.price
                , f.owner_id
                , date_trunc('second', f.on_market_since) AS on_market_since
                , b.amount AS bid_amount
            FROM 
                footballer AS f LEFT JOIN (
                SELECT *
                FROM bid
                WHERE bidder_id = %s
                ) AS b
            ON f.id = b.footballer_id
            WHERE
                on_market = TRUE
            ORDER BY owner_id, on_market_since 
            """,
            (player_id,)
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
    """Place or remove a bid on a footballer. To remove a bid, bid an amount of 0.
    Args:
        bid (BidRequest): The bid request containing player_id, footballer_id, and bid_amount.
    """
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
            DELETE FROM bid
            WHERE footballer_id = %s AND bidder_id = %s
            """,
            (bid.footballer_id, bid.player_id)
        )

        if bid.bid_amount == 0:
            conn.commit()
            cursor.close()
            conn.close()
            return {"status": "success", "message": "Bid removed successfully."}
        else:
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
    

class MarketFootballer(BaseModel):
    footballer_id: int
    player_id: int
    on_market: bool

@server_app.post("/edit_player")
def edit_player_status(market_footballer: MarketFootballer):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres_db"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432"),
        )
        cursor = conn.cursor()

        on_market_since = 'now()' if market_footballer.on_market else None

        cursor.execute(
            """
            UPDATE footballer
            SET 
                on_market = %s
                , on_market_since = %s
            WHERE id = %s;
            """,
            (market_footballer.on_market, on_market_since, market_footballer.footballer_id)
        )
        logger.info(f"Player {market_footballer.player_id} {'placed on' if market_footballer.on_market else 'removed from'} market")

        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": "Player status updated successfully."}
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {"status": "error", "message": str(e)}


@server_app.get('/leaderboard')
def leaderboard():
    """Get the leaderboard of players
    ."""
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
            SELECT 
                row_number() OVER (ORDER BY p.score DESC) AS position
                , p.name
                , coalesce(p.score, 0) AS score
                , coalesce(sv.squad_value, 0) AS squad_value
            FROM player AS p LEFT JOIN (
                SELECT owner_id, SUM(price) AS squad_value
                FROM footballer
                WHERE owner_id IS NOT NULL
                GROUP BY owner_id
            ) AS sv ON p.id = sv.owner_id
            ORDER BY position
            """
        )
        players = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"leaderboard": players}
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {"leaderboard": []}


def scrape_page(url):
    logger.debug(f"Fetching {url}")
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup