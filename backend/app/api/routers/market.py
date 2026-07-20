from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from .logger import logger
from backend.app.db.database import pg_connect, mongo_client
from backend.app.core.constants import BANK_NAME, MAX_DEBT_AS_VALUE_UNIT
from backend.app.models.footballer import Footballer
from backend.app.models.market import load_market
from backend.app.models.player import debit_player_value
from backend.app.api.routers.player import get_player_bid_sum, get_player_info, get_team_value


router = APIRouter(prefix="/market", tags=["market"])


@router.get("")
def market(league_id: int):
    """Get all footballers currently on the market.

    Args:
        league_id (int): The league ID to filter by.
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM footballer
            WHERE on_market = TRUE AND league_id = %s
            ORDER BY owner_id, on_market_since
            """,
            (league_id,)
        )
        footballers = cursor.fetchall()

        cursor.close()
        conn.close()
        return {
            "status": "success",
            "footballers": footballers,
            "columns": [
                "id",
                "url_name",
                "on_market",
                "on_market_since",
                "owner_id",
                "on_lineup",
            ]
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "footballers": []}


@router.get("/{player_id}")
def player_market(player_id: int, league_id: int):
    """Get all footballers currently on the market with bid info for a specific player.
    
    Args:
        player_id (int): The ID of the player to get bid info for.
        league_id (int): The league ID to filter by.
    """
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
                , COALESCE((f.owner_id = %s), FALSE) AS is_own
                , f_data.position
            FROM footballer AS f 
            LEFT JOIN footballer_data AS f_data ON f.id = f_data.id
            LEFT JOIN (
                SELECT *
                FROM bid
                WHERE bidder_id = %s AND active = TRUE AND league_id = %s AND timestamp <= now()
            ) AS b ON f.id = b.footballer_id AND f.league_id = b.league_id
            LEFT JOIN player ON player.id = f.owner_id AND player.league_id = f.league_id
            WHERE
                on_market = TRUE
                AND f.league_id = %s
            ORDER BY is_own ASC, (f.owner_id IS NULL) DESC, on_market_since DESC
            """,
            (player_id, player_id, league_id, league_id)
        )
        footballers = cursor.fetchall()
        market = load_market(league_id)
        market_closing_timestamp = market.closing_ts.isoformat() if market and getattr(market, "closing_ts", None) else None

        cursor.close()
        conn.close()
        return {
            "status": "success",
            "footballers": footballers,
            "market_closing_timestamp": market_closing_timestamp,
            "columns": [
                "id",
                "name",
                "value",
                "owner_name",
                "on_market_since",
                "bid_amount",
                "average_points",
                "total_points",
                "is_own",
                "position"
            ]
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "footballers": [], "market_closing_timestamp": None}


@router.get("/past_bids/")
def get_past_bids(league_id: int, limit: int = 20, offset: int = 0):
    conn = pg_connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM bid
        WHERE 
            league_id = %s
            AND active = false
            AND acquired_from IS NOT NULL
        """, (league_id,)
    )
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
	        COALESCE(p_from.name, 'League') AS "from"
            , COALESCE(p_to.name, 'League') AS "to"
            , fd.name
            , fd.id AS footballer_id
            , bid.amount
            , to_char(bid.timestamp, 'DD-MM-YYYY HH24:MI')
        FROM bid
            LEFT JOIN player AS p_to ON bid.bidder_id = p_to.id
            LEFT JOIN player AS p_from ON bid.acquired_from = p_from.id
            LEFT JOIN footballer_data AS fd ON bid.footballer_id = fd.id
        WHERE
            bid.acquired_from IS NOT NULL
            AND bid.active = false
            AND bid.league_id = %s
        ORDER BY bid.timestamp DESC
        LIMIT %s
        OFFSET %s
        """, (league_id, limit, offset)
    )

    bid_history = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "status": "success",
        "bid_history": bid_history,
        "columns": ["from_player", "to_player", "amount", "footballer_name", "footballer_id", "timestamp"],
        "meta": {
                "total": total,
                "limit": limit,
                "offset": offset,
            },
    }

class BidRequest(BaseModel):
    player_id: int
    footballer_id: int
    bid_amount: int
    league_id: int
    timestamp: datetime | None = None

@router.post("/bid")
def place_bid(bid: BidRequest):
    """Place or remove a bid on a footballer. To remove a bid, bid an amount of 0.
    Args:
        bid (BidRequest): The bid request containing player_id, footballer_id, bid_amount, and league_id.
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

        player_bid_sum = get_player_bid_sum(bid.player_id, bid.league_id)['total_bid_sum']
        player_budget = get_player_info(bid.player_id, bid.league_id)['player'][2]
        player_debt = player_bid_sum + bid.bid_amount - player_budget
        team_value = get_team_value(bid.player_id, bid.league_id)

        if bid.bid_amount < footballer.data['market_details'][-1]['value'] and bid.bid_amount != 0:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Bid amount is less than the footballer's market value."}
        elif bid.player_id == owner_id:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Cannot bid on your own footballer."}
        elif player_debt > MAX_DEBT_AS_VALUE_UNIT * team_value:
            cursor.close()
            conn.close()
            return {"status": "error", "message": f"Bid amount implies a greater debt ({player_debt:,.0f} €) than {MAX_DEBT_AS_VALUE_UNIT:.0%} of your team's value ({(team_value * MAX_DEBT_AS_VALUE_UNIT):,.0f} €)."}
        else:
            cursor.execute(
                """
                DELETE FROM bid
                WHERE footballer_id = %s AND bidder_id = %s AND league_id = %s
            """,
            (bid.footballer_id, bid.player_id, bid.league_id)
        )

        if bid.bid_amount == 0:
            conn.commit()
            cursor.close()
            conn.close()
            return {"status": "success", "message": "Bid removed successfully."}
        else:
            bid_timestamp = bid.timestamp or datetime.now(timezone.utc)
            if bid_timestamp.tzinfo is None:
                bid_timestamp = bid_timestamp.replace(tzinfo=timezone.utc)

            cursor.execute(
                """
                INSERT INTO bid (footballer_id, bidder_id, amount, timestamp, league_id, active)
                VALUES (%s, %s, %s, %s, %s, true)
                """,
                (bid.footballer_id, bid.player_id, bid.bid_amount, bid_timestamp, bid.league_id)
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
def reply_to_bid(bid_id: int, league_id: int, accept: bool):
    """Accept or reject a bid on a footballer.
    
    Args:
        bid_id (int): The ID of the bid to reply to.
        league_id (int): The ID of the league to filter by.
        accept (bool): True to accept the bid, False to reject it.
    """
    try:
        conn = pg_connect()        
        cursor = conn.cursor()
        
        cursor.execute(
                """
                SELECT
                    b.footballer_id
                    , b.bidder_id
                    , b.amount
                    , f.owner_id
                FROM bid AS b LEFT JOIN footballer AS f ON b.footballer_id = f.id
                WHERE b.id = %s AND f.league_id = %s
            """,
            (bid_id, league_id)
        )
        bid = cursor.fetchone()
        if not bid:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Bid not found."}
        
        footballer_id, bidder_id, amount, owner_id = bid

        if accept:
            cursor.execute(
                """
                UPDATE footballer
                SET owner_id = %s, on_market = FALSE, on_market_since = NULL
                WHERE id = %s AND league_id = %s;
                UPDATE bid
                SET active = false
                WHERE footballer_id = %s AND league_id = %s
                """,
                (bidder_id, footballer_id, league_id, footballer_id, league_id)
            )
            if bidder_id is not None:
                debit_player_value(bidder_id, amount)
            if owner_id is not None:
                debit_player_value(owner_id, -amount)

            logger.info(f"Bid accepted: Footballer {footballer_id} sold to Player {bidder_id} for {amount}")
        else:
            logger.info(f"Bid rejected: Footballer {footballer_id} bid from Player {bidder_id} for {amount} rejected")

            cursor.execute(
                """
                UPDATE bid
                SET active = false
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
def get_player_incoming_bids(player_id: int, league_id: int):
    """Get all incoming bids for a player's footballers.
    
    Args:
        player_id (int): The ID of the player to get incoming bids for.
        league_id (int): The league ID to filter by.
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
                , COALESCE(p.name, %s) AS bidder_name
                , fd.name AS footballer_name
                , b.amount
            FROM bid AS b
                LEFT JOIN footballer AS f ON b.footballer_id = f.id AND b.league_id = f.league_id
                LEFT JOIN footballer_data AS fd ON b.footballer_id = fd.id
                LEFT JOIN player AS p on b.bidder_id = p.id
            WHERE
                f.owner_id = %s
                AND b.league_id = %s
                AND b.active = TRUE
                AND b.timestamp <= now()
            ORDER BY footballer_id, b.timestamp DESC
            """,
            (BANK_NAME, player_id, league_id)
        )
        bids = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "bids": bids, "columns": ["bid_id", "timestamp", "footballer_id", "bidder_name", "footballer_name", "amount"]}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "bids": []}
    

@router.get("/outgoing_bids/{player_id}")
def get_player_outgoing_bids(player_id: int, league_id: int):
    """Get all outgoing bids made by a player.
    
    Args:
        player_id (int): The ID of the player to get outgoing bids for.
        league_id (int): The league ID to filter by.
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
                , COALESCE(p.name, %s) AS owner_name
                , fd.name AS footballer_name
                , b.amount
            FROM bid AS b
                LEFT JOIN footballer AS f ON b.footballer_id = f.id AND b.league_id = f.league_id
                LEFT JOIN footballer_data AS fd ON b.footballer_id = fd.id
                LEFT JOIN player AS p on f.owner_id = p.id
            WHERE
                b.bidder_id = %s
                AND b.league_id = %s
                AND b.active = TRUE
                AND b.timestamp <= now()
            ORDER BY footballer_id, b.timestamp DESC
            """,
            (BANK_NAME, player_id, league_id)
        )
        bids = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "bids": bids, "columns": ["bid_id", "timestamp", "footballer_id", "owner_name", "footballer_name", "amount"]}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "bids": []}


@router.get("/future_bids/{player_id}")
def get_player_future_bids(player_id: int, league_id: int):
    """Get all outgoing bids scheduled for the future."""
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                b.id AS bid_id
                , b.timestamp
                , f.id AS footballer_id
                , COALESCE(p.name, %s) AS owner_name
                , fd.name AS footballer_name
                , b.amount
            FROM bid AS b
                LEFT JOIN footballer AS f ON b.footballer_id = f.id AND b.league_id = f.league_id
                LEFT JOIN footballer_data AS fd ON b.footballer_id = fd.id
                LEFT JOIN player AS p on f.owner_id = p.id
            WHERE
                b.bidder_id = %s
                AND b.league_id = %s
                AND b.active = TRUE
                AND b.timestamp > now()
            ORDER BY b.timestamp ASC, footballer_id
            """,
            (BANK_NAME, player_id, league_id)
        )
        bids = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "bids": bids, "columns": ["bid_id", "timestamp", "footballer_id", "owner_name", "footballer_name", "amount"]}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "bids": []}


class ReleaseClauseRequest(BaseModel):
    player_id: int
    footballer_id: int

@router.post("/pay_release_clause")
def pay_release_clause(request: ReleaseClauseRequest):
    """Pay the release clause to acquire a footballer.
    
    Args:
        request (ReleaseClauseRequest): The request containing player_id and footballer_id.
        
    Returns:
        dict: A dictionary with status and message.
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        client = mongo_client()
        
        # Get footballer data
        cursor.execute(
            """
            SELECT
                owner_id
                , release_clause
            FROM footballer
            WHERE id = %s
            """,
            (request.footballer_id,)
        )
        
        result = cursor.fetchone()
        if not result:
            return {"status": "error", "message": "Footballer not found."}
        
        owner_id, release_clause = result
        
        # Cannot pay release clause if owner_id is NULL
        if owner_id is None:
            return {"status": "error", "message": "Release clause not available for this footballer."}
        
        # Cannot acquire your own footballer
        if owner_id == request.player_id:
            return {"status": "error", "message": "Cannot pay release clause for your own footballer."}
        
        # Transfer the footballer
        cursor.execute(
            """
            UPDATE footballer
            SET owner_id = %s, on_market = FALSE, on_market_since = NULL, on_lineup = FALSE
            WHERE id = %s
            """,
            (request.player_id, request.footballer_id)
        )
        
        cursor.execute(
            """
            UPDATE bid
            SET active = false
            WHERE footballer_id = %s
            """,
            (request.footballer_id,)
        )
        
        # Update player budgets
        debit_player_value(request.player_id, release_clause)
        debit_player_value(owner_id, -release_clause)
        
        conn.commit()
        
        logger.info(f"Release clause paid: Footballer {request.footballer_id} transferred from Player {owner_id} to Player {request.player_id} for {release_clause}")
        return {"status": "success", "message": f"Release clause paid successfully. Footballer acquired for €{release_clause:,.0f}."}
    except Exception as e:
        logger.error(f"Error paying release clause: {e}")
        if conn:
            conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        if client:
            client.close()
