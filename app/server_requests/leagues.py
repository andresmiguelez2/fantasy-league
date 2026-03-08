from fastapi import APIRouter, Depends
from aux.database import pg_connect
from .logger import logger
from .auth import get_current_user_from_token


router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("")
def get_all_leagues():
    """Get all available leagues."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM league ORDER BY id")
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


@router.get("/mine")
def get_my_leagues(current_user: dict = Depends(get_current_user_from_token)):
    """Get leagues that the authenticated user participates in."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ul.league_id, l.name, ul.player_id
            FROM user_leagues ul
            JOIN league l ON ul.league_id = l.id
            WHERE ul.user_id = %s
            ORDER BY l.name
            """,
            (current_user["id"],),
        )
        leagues = cursor.fetchall()
        cursor.close()
        conn.close()
        return {
            "status": "success",
            "leagues": [
                {"id": row[0], "name": row[1], "player_id": row[2]}
                for row in leagues
            ],
        }
    except Exception as e:
        logger.error(f"Error fetching user leagues: {e}")
        return {"status": "error", "leagues": []}
