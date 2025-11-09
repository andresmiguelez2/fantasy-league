from fastapi import FastAPI
from pydantic import BaseModel
from pymongo import MongoClient
import logging
import psycopg2
import os
from classes.footballer import Footballer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import imghdr
from bson.binary import Binary
from aux.aux_functions import extract_fixture_points


logger = logging.getLogger(__name__)

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

        client = MongoClient(f"mongodb://{os.getenv('MONGO_INITDB_ROOT_USERNAME')}:{os.getenv('MONGO_INITDB_ROOT_PASSWORD')}@mongodb:27017/fantasy_mongo_db?authSource=admin")
        db = client["FantasyMDB"]

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id
                , name
                , on_market
                , on_market_since
            FROM footballer WHERE owner_id = %s ORDER BY id
            """,
            (player_id,),
        )
        players = cursor.fetchall()
        cursor.close()
        conn.close()

        player_data = list()
        for player in players:
            value = db.footballer.find({"id": player[0]})[0]['market_details'][-1]['value']
            team = db.footballer.find({"id": player[0]})[0]['team']
            player_data.append((player[0], player[1], team, value, player[2], player[3]))

        return {"footballers": player_data}
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {"footballers": []}
    

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
        return {"footballers": players}
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {"footballers": []}
    

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

        client = MongoClient(f"mongodb://{os.getenv('MONGO_INITDB_ROOT_USERNAME')}:{os.getenv('MONGO_INITDB_ROOT_PASSWORD')}@mongodb:27017/fantasy_mongo_db?authSource=admin")
        db = client["FantasyMDB"]

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                f.id
                , f.name
                , player.name
                , date_trunc('second', f.on_market_since) AS on_market_since
                , b.amount AS bid_amount
            FROM 
                footballer AS f
                LEfT JOIN player ON f.owner_id = player.id
                LEFT JOIN (
                    SELECT *
                    FROM bid
                    WHERE bidder_id = %s
                ) AS b ON f.id = b.footballer_id
            WHERE
                on_market = TRUE
            ORDER BY owner_id, on_market_since 
            """,
            (player_id,)
        )
        players = cursor.fetchall()
        
        player_data = list()
        for player in players:
            value = db.footballer.find({"id": player[0]})[0]['market_details'][-1]['value']
            average_points = db.footballer.find({"id": player[0]})[0]['average_points']
            total_points = db.footballer.find({"id": player[0]})[0]['total_points']
            player_data.append((player[0], player[1], value, player[2], player[3], player[4], average_points, total_points))

        cursor.close()
        conn.close()
        return {"footballers": player_data}
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {"footballers": []}


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

        client = MongoClient(f"mongodb://{os.getenv('MONGO_INITDB_ROOT_USERNAME')}:{os.getenv('MONGO_INITDB_ROOT_PASSWORD')}@mongodb:27017/fantasy_mongo_db?authSource=admin")

        cursor.execute(
                """
                SELECT name, url_name, owner_id
                FROM footballer
                WHERE id = %s
            """,
            (bid.footballer_id,)
        )
        full_name, url_name, owner_id = cursor.fetchone()

        footballer = Footballer(obtain_data=False, full_name=full_name)
        footballer.url_name = url_name
        footballer.id = bid.footballer_id
        footballer.get_player_data()
        footballer.update_in_db(client)

        if bid.bid_amount < footballer.data['market_details'][-1]['value'] and bid.bid_amount != 0:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Bid amount is less than the footballer's market value."}
        elif bid.player_id == owner_id:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Cannot bid on your own footballer."}
        else:
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
            WHERE id = %s and owner_id = %s;
            """,
            (market_footballer.on_market, on_market_since, market_footballer.footballer_id, market_footballer.player_id)
        )
        affected = cursor.rowcount

        if affected == 0:
            logger.warning(f"Player {market_footballer.player_id} not found or not owned by user.")
            msg = {"status": "error", "message": "Player not found or not owned by user."}
        else:
            logger.info(f"Player {market_footballer.player_id} {'placed on' if market_footballer.on_market else 'removed from'} market")
            msg = {"status": "success", "message": "Player status updated successfully."}

        conn.commit()
        cursor.close()
        conn.close()
        
        return msg
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

        client = MongoClient(f"mongodb://{os.getenv('MONGO_INITDB_ROOT_USERNAME')}:{os.getenv('MONGO_INITDB_ROOT_PASSWORD')}@mongodb:27017/fantasy_mongo_db?authSource=admin")
        db = client["FantasyMDB"]

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id
                , name
                , points
            FROM player
            ORDER BY points DESC
            """
        )
        players = cursor.fetchall()

        player_data = list()
        for player in players:
            cursor.execute(
                """
                SELECT 
                    id
                FROM footballer
                where owner_id = %s
                """,
                (player[0],)
            )
            footballers = cursor.fetchall()

            team_value = 0
            for footballer_id in footballers:
                team_value += db.footballer.find({"id": footballer_id[0]})[0]['market_details'][-1]['value']

            player_data.append((player[0], player[1], player[2], team_value))

        cursor.close()
        conn.close()
        return {"leaderboard": player_data}
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {"leaderboard": []}
    

@server_app.get("/players/{player_id}")
def get_player_info(player_id: int):
    """Get information about a specific player."""
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
            FROM player
            WHERE id = %s
            """,
            (player_id,)
        )
        player = cursor.fetchone()
        cursor.close()
        conn.close()

        if player is None:
            return {"status": "error", "message": "Player not found."}

        return {
            "status": "success",
            "player": player
        }
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return {"status": "error", "message": str(e)}
    

@server_app.get("/footballers/{footballer_id}")
def get_footballer_info(footballer_id: int):
    """Get information about a specific footballer."""
    try:
        client = MongoClient(f"mongodb://{os.getenv('MONGO_INITDB_ROOT_USERNAME')}:{os.getenv('MONGO_INITDB_ROOT_PASSWORD')}@mongodb:27017/fantasy_mongo_db?authSource=admin")
        db = client["FantasyMDB"]

        footballer = db.footballer.find_one({"id": footballer_id})
        client.close()

        if footballer is None:
            return {"status": "error", "message": "Footballer not found."}

        del footballer['image_binary'] # Remove image binary data for efficiency

        return {
            "status": "success",
            "footballer_info": {
                "name": footballer['name'],
                "team": footballer['team'],
                "total_points": footballer['total_points'],
                "average_points": footballer['average_points'],
                "market_value": footballer['market_details'][-1]['value'],
                "market_details": footballer['market_details'],
                "fixture_breakdown": extract_fixture_points(footballer['fixture_breakdown']),
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving footballer info: {e}")
        return {"status": "error", "message": str(e)}
    

@server_app.get("/images/{footballer_id}")
def get_footballer_image(footballer_id: int):
    """Return the footballer's image as raw bytes (with proper Content-Type)."""
    try:
        client = MongoClient(f"mongodb://{os.getenv('MONGO_INITDB_ROOT_USERNAME')}:{os.getenv('MONGO_INITDB_ROOT_PASSWORD')}@mongodb:27017/fantasy_mongo_db?authSource=admin")
        db = client["FantasyMDB"]

        footballer = db.footballer.find_one({"id": footballer_id})
        if footballer is None:
            client.close()
            return {"status": "error", "message": "Footballer not found."}

        img_field = footballer.get("image_binary")
        if img_field is None:
            client.close()
            return {"status": "error", "message": "No image found for this footballer."}

        # Convert bson.Binary to raw bytes if necessary
        img_bytes = bytes(img_field)

        # Try to detect image type
        fmt = imghdr.what(None, img_bytes)
        content_type = f"image/{fmt}" if fmt else "application/octet-stream"

        client.close()
        return Response(content=img_bytes, media_type=content_type)

    except Exception as e:
        logger.error(f"Error retrieving footballer image: {e}")
        return {"status": "error", "message": str(e)}