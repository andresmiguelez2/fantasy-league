from fastapi import APIRouter
from backend.app.db.database import pg_connect
from .logger import logger


router = APIRouter(prefix="/squad", tags=["squad"])


@router.get("/{player_id}")
def squad(player_id: int, league_id: int):
    """Get the squad of a player.

    Args:
        player_id (int): The player ID.
        league_id (int): The league ID to filter by.
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                f.id
                , fd.name
                , fd.team
                , fd.value
                , fd.total_points
                , fd.average_points
                , f.on_market
                , f.on_market_since
                , fd.position
                , fd.availability
            FROM footballer f LEFT JOIN footballer_data fd ON f.id = fd.id
            WHERE f.owner_id = %s AND f.league_id = %s
            ORDER BY fd.position, fd.name
            """,
            (player_id, league_id),
        )
        footballers = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "footballers": footballers,
            "columns": [
                "id",
                "name",
                "team",
                "value",
                "total_points",
                "average_points",
                "on_market",
                "on_market_since",
                "position",
                "availability"
            ]
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "footballers": []}