from fastapi import APIRouter
from aux.database import pg_connect
from .logger import logger


router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("")
def get_leagues():
    """Get all available leagues."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name
            FROM league
            ORDER BY id
            """
        )
        leagues = cursor.fetchall()
        cursor.close()
        conn.close()
        return {
            "status": "success",
            "leagues": [{"id": row[0], "name": row[1]} for row in leagues],
        }
    except Exception as e:
        logger.error(f"Error fetching leagues: {e}")
        return {"status": "error", "leagues": []}


@router.get("/{league_id}")
def get_league(league_id: int):
    """Get details of a specific league."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name
            FROM league
            WHERE id = %s
            """,
            (league_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return {"status": "error", "message": "League not found."}
        return {"status": "success", "league": {"id": row[0], "name": row[1]}}
    except Exception as e:
        logger.error(f"Error fetching league {league_id}: {e}")
        return {"status": "error", "message": str(e)}
