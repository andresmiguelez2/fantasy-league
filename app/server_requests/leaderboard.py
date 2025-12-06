from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from .logger import logger


router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get('')
def leaderboard():
    """Get the leaderboard of players
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                -- row_number() OVER (ORDER BY points DESC) AS rank
                player.id
                , player.name
                , player.points
                , f.team_value
            FROM player
            LEFT JOIN (
                SELECT
                    footballer.owner_id
                    , SUM(footballer_data.value) AS team_value
                FROM footballer JOIN footballer_data ON footballer.id = footballer_data.id
                GROUP BY footballer.owner_id
            ) AS f ON player.id = f.owner_id
            ORDER BY points DESC
            """
        )
        players = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "leaderboard": players}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "leaderboard": []}