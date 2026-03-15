from fastapi import APIRouter
from aux.database import pg_connect
from .logger import logger


router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("")
def get_leagues():
    """Get all leagues."""
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
        logger.error(f"Error retrieving leagues: {e}")
        return {"status": "error", "leagues": []}
