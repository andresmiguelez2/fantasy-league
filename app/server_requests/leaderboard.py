from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from .logger import logger


router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get('/{fixture_id}')
def leaderboard(fixture_id: str):
    """Get the leaderboard of players
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()

        if fixture_id == "total":
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
        else:
            cursor.execute(
                """
                SELECT
                    player.id
                    , player.name
                    , fixture.points
                    , f.team_value
                FROM player
                LEFT JOIN (
                    SELECT
                        footballer.owner_id
                        , SUM(footballer_data.value) AS team_value
                    FROM footballer JOIN footballer_data ON footballer.id = footballer_data.id
                    GROUP BY footballer.owner_id
                ) AS f ON player.id = f.owner_id
                RIGHT JOIN (
                    SELECT
                        player_id
                        , COALESCE(points, 0) AS points
                    FROM fixture_details
                    WHERE fixture_n = %s
                ) AS fixture ON fixture.player_id = player.id
                ORDER BY points DESC
                """,
                (fixture_id,)
            )
        
        players = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "leaderboard": players, "columns": ["id", "name", "points", "team_value"]}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "leaderboard": []}