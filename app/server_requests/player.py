from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from .logger import logger


router = APIRouter(prefix="/player", tags=["player"])


@router.get('/{player_id}')
def get_player_info(player_id: int):
    """Get the player information
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id
                , name
                , budget
                , points
            FROM player
            WHERE id = %s
            """,
            (player_id,),
        )
        player = cursor.fetchone()

        cursor.close()
        conn.close()
        return {"status": "success", "player": player}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "player": None}