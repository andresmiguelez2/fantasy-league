from fastapi import APIRouter, Query
from aux.database import pg_connect
from .logger import logger


router = APIRouter(prefix="/leagues", tags=["leagues"])


def _get_player_leagues(player_id: int):
    """Get all leagues."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT league.id, league.name
            FROM league RIGHT JOIN player on player.league_id = league.id
            WHERE player.id = %s
            ORDER BY id
            """, (player_id,)
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


@router.get("")
def get_player_leagues_query(player_id: int = Query(...)):
    return _get_player_leagues(player_id)


@router.get("/{player_id}")
def get_player_leagues(player_id: int):
    return _get_player_leagues(player_id)
