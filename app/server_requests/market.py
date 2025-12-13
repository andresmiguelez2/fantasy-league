from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from .logger import logger
from pydantic import BaseModel
from classes.footballer import Footballer


router = APIRouter(prefix="/market", tags=["market"])


@router.get("")
def market():
    """Get all footballers currently on the market."""
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM footballer
            WHERE on_market = TRUE
            ORDER BY owner_id, on_market_since 
            """
        )
        footballers = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "footballers": footballers}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "footballers": []}


@router.get("/{player_id}")
def player_market(player_id: int):
    """Get all footballers currently on the market with bid info for a specific player.
    
    Args:
        player_id (int): The ID of the player to get bid info for."""
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                f.id
                , f_data.name
                , f_data.value
                , player.name
                , date_trunc('second', f.on_market_since) AS on_market_since
                , b.amount AS bid_amount
                , f_data.average_points
                , f_data.total_points
            FROM footballer AS f 
            LEFT JOIN footballer_data AS f_data ON f.id = f_data.id
            LEFT JOIN (
                SELECT *
                FROM bid
                WHERE bidder_id = %s
            ) AS b ON f.id = b.footballer_id
            LEFT JOIN player ON player.id = f.owner_id
            WHERE
                on_market = TRUE
                AND (f.owner_id IS NULL OR f.owner_id != %s)
            ORDER BY on_market_since DESC, owner_id 
            """,
            (player_id, player_id)
        )
        footballers = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "footballers": footballers}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "footballers": []}


class BidRequest(BaseModel):
    player_id: int
    footballer_id: int
    bid_amount: int

@router.post("/bid")
def place_bid(bid: BidRequest):
    """Place or remove a bid on a footballer. To remove a bid, bid an amount of 0.
    Args:
        bid (BidRequest): The bid request containing player_id, footballer_id, and bid_amount.
    """
    try:
        conn = pg_connect()        
        cursor = conn.cursor()
        
        cursor.execute(
                """
                SELECT footballer_data.FULL_name, footballer.url_name, footballer.owner_id
                FROM footballer LEFT JOIN footballer_data ON footballer.id = footballer_data.id
                WHERE footballer.id = %s
            """,
            (bid.footballer_id,)
        )
        full_name, url_name, owner_id = cursor.fetchone()

        footballer = Footballer(obtain_data=False, full_name=full_name)
        footballer.url_name = url_name
        footballer.id = bid.footballer_id
        footballer.get_player_data()

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
            logger.info(f"Received bid: Player {bid.player_id} bids {bid.bid_amount} on footballer {bid.footballer_id}")
            conn.commit()
            cursor.close()
            conn.close()
            return {"status": "success", "message": "Bid placed successfully."}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}
 

@router.post("/reply_to_bid/{bid_id}")
def reply_to_bid(bid_id: int, accept: bool):
    """Accept or reject a bid on a footballer.
    
    Args:
        bid_id (int): The ID of the bid to reply to.
        accept (bool): True to accept the bid, False to reject it.
    """
    try:
        conn = pg_connect()        
        cursor = conn.cursor()
        
        cursor.execute(
                """
                SELECT footballer_id, bidder_id, amount
                FROM bid
                WHERE id = %s
            """,
            (bid_id,)
        )
        bid = cursor.fetchone()
        if not bid:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Bid not found."}
        
        footballer_id, bidder_id, amount = bid

        if accept:
            cursor.execute(
                """
                UPDATE footballer
                SET owner_id = %s, on_market = FALSE, on_market_since = NULL
                WHERE id = %s
            """,
            (bidder_id, footballer_id)
        )
            logger.info(f"Bid accepted: Footballer {footballer_id} sold to Player {bidder_id} for {amount}")
        else:
            logger.info(f"Bid rejected: Footballer {footballer_id} bid from Player {bidder_id} for {amount} rejected")

        cursor.execute(
            """
            DELETE FROM bid
            WHERE id = %s
            """,
            (bid_id,)
        )

        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": "Bid reply processed successfully."}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/incoming_bids/{player_id}")
def get_player_incoming_bids(player_id: int):
    """Get all incoming bids for a player's footballers.
    
    Args:
        player_id (int): The ID of the player to get incoming bids for.
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                b.id AS bid_id
                , b.timestamp
                , f.id AS footballer_id
                , b.bidder_id
                , fd.name
                , b.amount
            FROM bid AS b
                LEFT JOIN footballer AS f ON b.footballer_id = f.id
                LEFT JOIN footballer_data AS fd ON b.footballer_id = fd.id
            WHERE f.owner_id = %s
            ORDER BY footballer_id, b.timestamp DESC
            """,
            (player_id,)
        )
        bids = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "bids": bids, "columns": ["bid_id", "timestamp", "footballer_id", "bidder_id", "footballer_name", "amount"]}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "bids": []}
    

@router.get("/outgoing_bids/{player_id}")
def get_player_outgoing_bids(player_id: int):
    """Get all outgoing bids made by a player.
    
    Args:
        player_id (int): The ID of the player to get outgoing bids for.
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                b.id AS bid_id
                , b.timestamp
                , f.id AS footballer_id
                , f.owner_id
                , fd.name
                , b.amount
            FROM bid AS b
                LEFT JOIN footballer AS f ON b.footballer_id = f.id
                LEFT JOIN footballer_data AS fd ON b.footballer_id = fd.id
            WHERE b.bidder_id = %s
            ORDER BY footballer_id, b.timestamp DESC
            """,
            (player_id,)
        )
        bids = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "bids": bids, "columns": ["bid_id", "timestamp", "footballer_id", "owner_id", "footballer_name", "amount"]}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "bids": []}