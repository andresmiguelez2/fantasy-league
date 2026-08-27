from datetime import datetime, timedelta, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.api.routers.player import (
    get_player_bid_sum,
    get_player_info,
    get_team_value,
)
from backend.app.core.constants import (
    BANK_NAME,
    MAX_DEBT_AS_VALUE_UNIT,
    MIN_RELEASE_CLAUSE_VALUE,
    RELEASE_CLAUSE_DAYS,
    BID_EXPIRATION_DAYS,
)
from backend.app.db.database import mongo_client, pg_connect
from backend.app.models.footballer import Footballer
from backend.app.models.market import load_market
from backend.app.models.player import debit_player_value

from .logger import logger

router = APIRouter(prefix="/market", tags=["market"])


def mark_expired_bids_inactive(league_id: int):
    """Mark bids as inactive if they have expired based on BID_EXPIRATION_DAYS."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        expiration_threshold = datetime.now(tz=timezone.utc) - timedelta(
            days=BID_EXPIRATION_DAYS
        )
        cursor.execute(
            """
            UPDATE bid
            SET active = FALSE
            WHERE
                league_id = %s
                AND active = TRUE
                AND timestamp <= %s
            """,
            (league_id, expiration_threshold),
        )
        expired_count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        if expired_count > 0:
            logger.info(
                f"Marked {expired_count} expired bids as inactive. League {league_id}."
            )
        return expired_count
    except Exception as e:
        logger.error(f"Error marking expired bids as inactive: {e}")
        return 0


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
            (league_id,),
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
            ],
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
                , f_data.availability
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
            (player_id, player_id, league_id, league_id),
        )
        footballers = cursor.fetchall()
        market = load_market(league_id)
        market_closing_timestamp = (
            market.closing_ts.isoformat()
            if market and getattr(market, "closing_ts", None)
            else None
        )

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
                "position",
                "availability",
            ],
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
        """,
        (league_id,),
    )
    total = cursor.fetchone()[0]

    cursor.execute(
        """
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
        """,
        (league_id, limit, offset),
    )

    bid_history = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "status": "success",
        "bid_history": bid_history,
        "columns": [
            "from_player",
            "to_player",
            "amount",
            "footballer_name",
            "footballer_id",
            "timestamp",
        ],
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
    bid_id: int | None = None
    timestamp: datetime | None = None
    release_clause: bool = False


def _player_has_enough_budget(
    player_id: int,
    league_id: int,
    new_bid_amount: int = 0,
    current_bid_amount: int = 0,
    adjust_team_value: bool = True,
):
    """Check whether the player can cover active bid commitments."""
    player_bid_sum = get_player_bid_sum(player_id, league_id)["total_bid_sum"]
    player_budget = get_player_info(player_id, league_id)["player"][2]
    adjusted_bid_sum = player_bid_sum - current_bid_amount + new_bid_amount
    player_debt = adjusted_bid_sum - player_budget
    team_value = get_team_value(player_id, league_id) if adjust_team_value else 0

    if player_debt > MAX_DEBT_AS_VALUE_UNIT * team_value:
        if adjust_team_value:
            return False, (
                f"Bid amount implies a greater debt ({player_debt:,.0f} €) than "
                f"{MAX_DEBT_AS_VALUE_UNIT:.0%} of your team's value "
                f"({(team_value * MAX_DEBT_AS_VALUE_UNIT):,.0f} €)."
            )
        else:
            return False, f"Bid amount implies a debt ({player_debt:,.0f} €)."

    return True, None


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
                WHERE footballer.id = %s AND footballer.league_id = %s
            """,
            (bid.footballer_id, bid.league_id),
        )
        full_name, url_name, owner_id = cursor.fetchone()

        footballer = Footballer(obtain_data=False, full_name=full_name)
        footballer.url_name = url_name
        footballer.id = bid.footballer_id
        footballer.get_player_data()

        if bid.bid_id is not None:
            cursor.execute(
                """
                SELECT id, amount
                FROM bid
                WHERE
                    id = %s
                    AND footballer_id = %s
                    AND bidder_id = %s
                    AND league_id = %s
                    AND active = true
                """,
                (bid.bid_id, bid.footballer_id, bid.player_id, bid.league_id),
            )
        else:
            cursor.execute(
                """
                SELECT id, amount
                FROM bid
                WHERE
                    footballer_id = %s
                    AND bidder_id = %s
                    AND league_id = %s
                    AND active = true
                ORDER BY timestamp DESC, id DESC
                LIMIT 1
                """,
                (bid.footballer_id, bid.player_id, bid.league_id),
            )
        existing_bid = cursor.fetchone()
        if bid.bid_id is not None and existing_bid is None:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Bid not found."}
        existing_bid_id = existing_bid[0] if existing_bid else None
        existing_bid_amount = existing_bid[1] if existing_bid else 0

        has_enough_budget, budget_error = _player_has_enough_budget(
            bid.player_id,
            bid.league_id,
            bid.bid_amount,
            existing_bid_amount,
            adjust_team_value=owner_id is not None,
        )

        if (
            bid.bid_amount < footballer.data["market_details"][-1]["value"]
            and bid.bid_amount != 0
        ):
            cursor.close()
            conn.close()
            return {
                "status": "error",
                "message": "Bid amount is less than the footballer's market value.",
            }
        elif bid.player_id == owner_id:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Cannot bid on your own footballer."}
        elif not has_enough_budget:
            cursor.close()
            conn.close()
            return {"status": "error", "message": budget_error}

        if bid.bid_amount == 0:
            if existing_bid_id is not None:
                cursor.execute(
                    """
                    UPDATE bid
                    SET active = false
                    WHERE id = %s
                    """,
                    (existing_bid_id,),
                )
            conn.commit()
            cursor.close()
            conn.close()
            return {"status": "success", "message": "Bid removed successfully."}
        else:
            bid_timestamp = bid.timestamp or datetime.now(timezone.utc)
            if bid_timestamp.tzinfo is None:
                bid_timestamp = bid_timestamp.replace(tzinfo=timezone.utc)

            if existing_bid_id is not None:
                cursor.execute(
                    """
                    UPDATE bid
                    SET amount = %s, timestamp = %s, release_clause = %s
                    WHERE id = %s
                    """,
                    (
                        bid.bid_amount,
                        bid_timestamp,
                        bid.release_clause,
                        existing_bid_id,
                    ),
                )
                logger.info(
                    f"Updated bid: Player {bid.player_id} bids {bid.bid_amount} on footballer {bid.footballer_id}"
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO bid (footballer_id, bidder_id, amount, timestamp, league_id, active, release_clause)
                    VALUES (%s, %s, %s, %s, %s, true, %s)
                    """,
                    (
                        bid.footballer_id,
                        bid.player_id,
                        bid.bid_amount,
                        bid_timestamp,
                        bid.league_id,
                        bid.release_clause,
                    ),
                )
                logger.info(
                    f"Received bid: Player {bid.player_id} bids {bid.bid_amount} on footballer {bid.footballer_id}"
                )
            conn.commit()
            cursor.close()
            conn.close()
            return {"status": "success", "message": "Bid placed successfully."}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "message": 'Other error'}


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
                    , p.budget
                FROM 
                    bid AS b LEFT JOIN footballer AS f ON b.footballer_id = f.id 
                    LEFT JOIN player AS p on b.bidder_id = p.id AND b.league_id = p.league_id
                WHERE b.id = %s AND f.league_id = %s
            """,
            (bid_id, league_id),
        )
        bid = cursor.fetchone()
        if not bid:
            cursor.close()
            conn.close()
            return {"status": "error", "message": "Bid not found."}

        footballer_id, bidder_id, amount, owner_id, budget = bid

        if accept:
            if budget is not None:
                has_enough_budget, budget_error = _player_has_enough_budget(
                    bidder_id,
                    league_id,
                )
                if not has_enough_budget:
                    cursor.close()
                    conn.close()
                    return {"status": "error", "message": budget_error}

            cursor.execute(
                """
                UPDATE footballer
                SET owner_id = %s, on_market = FALSE, on_market_since = NULL
                WHERE id = %s AND league_id = %s;
                UPDATE bid
                SET active = false, acquired_from = %s
                WHERE footballer_id = %s AND league_id = %s
                """,
                (
                    bidder_id,
                    footballer_id,
                    league_id,
                    owner_id,
                    footballer_id,
                    league_id,
                ),
            )
            if budget is not None:
                debit_player_value(bidder_id, amount)
            if owner_id is not None:
                debit_player_value(owner_id, -amount)

            logger.info(
                f"Bid accepted: Footballer {footballer_id} sold to Player {bidder_id} for {amount}"
            )
        else:
            logger.info(
                f"Bid rejected: Footballer {footballer_id} bid from Player {bidder_id} for {amount} rejected"
            )

            cursor.execute(
                """
                UPDATE bid
                SET active = false
                WHERE id = %s
                """,
                (bid_id,),
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
        mark_expired_bids_inactive(league_id)
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
            (BANK_NAME, player_id, league_id),
        )
        bids = cursor.fetchall()

        cursor.close()
        conn.close()
        return {
            "status": "success",
            "bids": bids,
            "columns": [
                "bid_id",
                "timestamp",
                "footballer_id",
                "bidder_name",
                "footballer_name",
                "amount",
            ],
        }
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
        mark_expired_bids_inactive(league_id)
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
                , f.owner_id
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
            (BANK_NAME, player_id, league_id),
        )
        bids = cursor.fetchall()

        cursor.close()
        conn.close()
        return {
            "status": "success",
            "bids": bids,
            "columns": [
                "bid_id",
                "timestamp",
                "footballer_id",
                "owner_name",
                "footballer_name",
                "amount",
                "owner_id",
            ],
        }
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
            (BANK_NAME, player_id, league_id),
        )
        bids = cursor.fetchall()

        cursor.close()
        conn.close()
        return {
            "status": "success",
            "bids": bids,
            "columns": [
                "bid_id",
                "timestamp",
                "footballer_id",
                "owner_name",
                "footballer_name",
                "amount",
            ],
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "bids": []}


class ReleaseClauseRequest(BaseModel):
    player_id: int
    footballer_id: int
    league_id: int | None


class ScheduleReleaseClauseBidRequest(BaseModel):
    player_id: int
    footballer_id: int
    bid_amount: int
    league_id: int


@router.post("/schedule_release_clause_bid")
def schedule_release_clause_bid(request: ScheduleReleaseClauseBidRequest):
    conn = None
    cursor = None
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                owner_id
                , release_clause
                , acquisition_ts
                , COALESCE(acquisition_ts < now() - make_interval(days => %s), FALSE) AS rc_available
            FROM footballer
            WHERE id = %s AND league_id = %s
            """,
            (RELEASE_CLAUSE_DAYS, request.footballer_id, request.league_id),
        )
        result = cursor.fetchone()
        if not result:
            return {"status": "error", "message": "Footballer not found."}

        owner_id, release_clause_amount, acquisition_ts, rc_available = result
        if owner_id is None:
            return {
                "status": "error",
                "message": "Release clause not available for this footballer.",
            }
        if owner_id == request.player_id:
            return {
                "status": "error",
                "message": "Cannot schedule a release clause bid for your own footballer.",
            }
        if rc_available:
            return {
                "status": "error",
                "message": "Release clause is already available. Pay it directly instead.",
            }
        if release_clause_amount is None:
            return {
                "status": "error",
                "message": "Release clause not configured for this footballer.",
            }
        if acquisition_ts is None:
            return {
                "status": "error",
                "message": "Release clause schedule cannot be computed for this footballer.",
            }

        if acquisition_ts.tzinfo is None:
            acquisition_ts = acquisition_ts.replace(tzinfo=timezone.utc)

        scheduled_timestamp = acquisition_ts + timedelta(
            days=RELEASE_CLAUSE_DAYS, seconds=1
        )
        now_utc = datetime.now(timezone.utc)
        if scheduled_timestamp <= now_utc:
            logger.warning(
                "Computed release clause schedule timestamp is in the past for footballer %s in league %s. "
                "Falling back to now + 1 second.",
                request.footballer_id,
                request.league_id,
            )
            scheduled_timestamp = now_utc + timedelta(seconds=1)

        response = place_bid(
            BidRequest(
                player_id=request.player_id,
                footballer_id=request.footballer_id,
                bid_amount=request.bid_amount,
                league_id=request.league_id,
                timestamp=scheduled_timestamp,
                release_clause=True,
            )
        )
        if response.get("status") != "success":
            return {
                "status": "error",
                "message": "Unable to schedule release clause bid.",
            }

        return {
            "status": "success",
            "message": "Release clause bid scheduled successfully.",
            "scheduled_timestamp": scheduled_timestamp.isoformat(),
        }
    except Exception as e:
        logger.error(f"Error scheduling release clause bid: {e}")
        return {"status": "error", "message": "Unable to schedule release clause bid."}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


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
            WHERE id = %s AND league_id = %s
            """,
            (request.footballer_id, request.league_id),
        )

        result = cursor.fetchone()
        if not result:
            return {"status": "error", "message": "Footballer not found."}

        owner_id, release_clause = result

        # Cannot pay release clause if owner_id is NULL
        if owner_id is None:
            return {
                "status": "error",
                "message": "Release clause not available for this footballer.",
            }

        # Cannot acquire your own footballer
        if owner_id == request.player_id:
            return {
                "status": "error",
                "message": "Cannot pay release clause for your own footballer.",
            }

        has_enough_budget, budget_error = _player_has_enough_budget(
            request.player_id,
            request.league_id,
            new_bid_amount=release_clause,
            current_bid_amount=0,
            adjust_team_value=False,  # Do not adjust team value when paying release clause
        )
        if not has_enough_budget:
            return {"status": "error", "message": budget_error}

        # Transfer the footballer
        cursor.execute(
            """
            UPDATE footballer
            SET owner_id = %s, on_market = FALSE, on_market_since = NULL, on_lineup = FALSE
            WHERE id = %s AND league_id = %s
            """,
            (request.player_id, request.footballer_id, request.league_id),
        )

        cursor.execute(
            """
            INSERT INTO bid (amount, timestamp, bidder_id, footballer_id, league_id, active, acquired_from, release_clause)
            VALUES (%s, now(), %s, %s, %s, FALSE, %s, TRUE)
            """,
            (
                release_clause,
                request.player_id,
                request.footballer_id,
                request.league_id,
                owner_id,
            ),
        )

        # Update player budgets
        debit_player_value(request.player_id, release_clause)
        debit_player_value(owner_id, -release_clause)

        conn.commit()

        logger.info(
            f"Release clause paid: Footballer {request.footballer_id} transferred from Player {owner_id} to Player {request.player_id} for {release_clause}"
        )
        return {
            "status": "success",
            "message": f"Release clause paid successfully. Footballer acquired for €{release_clause:,.0f}.",
        }
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


@router.post("/increment_release_clause/{footballer_id}")
def increment_release_clause(
    footballer_id: int, league_id: int, player_id: int, value: int
):
    """Increment the release clause of a footballer."""
    try:
        if value <= 0:
            return {"status": "error", "message": "Increment must be a positive value."}

        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT f.owner_id, f.release_clause, fd.value
            FROM footballer AS f JOIN footballer_data AS fd ON f.id = fd.id
            WHERE f.id = %s AND f.league_id = %s
            """,
            (footballer_id, league_id),
        )
        row = cursor.fetchone()

        if not row:
            return {"status": "error", "message": "Footballer not found."}

        owner_id, current_release_clause, footballer_value = row

        if owner_id != player_id:
            return {
                "status": "error",
                "message": "You can only increment the release clause of your own footballer.",
            }

        has_enough_budget, _ = _player_has_enough_budget(player_id, league_id, value)
        if not has_enough_budget:
            return {
                "status": "error",
                "message": "You do not have enough budget to increment the release clause.",
            }

        new_release_clause = (
            max(current_release_clause or 0, MIN_RELEASE_CLAUSE_VALUE, footballer_value)
            + 2 * value
        )

        cursor.execute(
            """
            UPDATE footballer
            SET release_clause = %s
            WHERE id = %s AND league_id = %s
            """,
            (new_release_clause, footballer_id, league_id),
        )
        debit_player_value(player_id, value)

        conn.commit()

        logger.info(
            f"Release clause incremented: Footballer {footballer_id} by Player {player_id} "
            f"from {current_release_clause} to {new_release_clause}"
        )
        return {
            "status": "success",
            "message": f"Release clause updated to €{new_release_clause:,.0f}.",
            "release_clause": new_release_clause,
        }
    except Exception as e:
        logger.error(f"Error incrementing release clause: {e}")
        if conn:
            conn.rollback()
        return {
            "status": "error",
            "message": "An error occurred while incrementing the release clause.",
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
