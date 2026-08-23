from fastapi import APIRouter
from backend.app.db.database import pg_connect, mongo_client
from .logger import logger

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/{fixture_id}")
def leaderboard(fixture_id: str, league_id: int):
    """Get the leaderboard of players

    Args:
        fixture_id (str): The fixture ID or 'total' for the overall leaderboard.
        league_id (int): The league ID to filter by.
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()

        if fixture_id == "total":
            cursor.execute(
                """
                    SELECT
                        player.id
                        , player.name
                        , player.points
                        , f.team_value
                        , player.picture_url
                    FROM player
                    LEFT JOIN (
                        SELECT
                            footballer.owner_id
                            , SUM(footballer_data.value) AS team_value
                        FROM footballer JOIN footballer_data ON footballer.id = footballer_data.id
                        WHERE footballer.league_id = %s
                        GROUP BY footballer.owner_id
                    ) AS f ON player.id = f.owner_id
                    WHERE
                        player.league_id = %s
                        AND player.points IS NOT NULL
                        AND player.budget IS NOT NULL
                        AND player.lineup IS NOT NULL
                    ORDER BY player.points DESC
                    """,
                (league_id, league_id),
            )
        else:
            cursor.execute(
                """
                    SELECT
                        player.id
                        , player.name
                        , fixture.points
                        , f.team_value
                        , player.picture_url
                    FROM player
                    LEFT JOIN (
                        SELECT
                            footballer.owner_id
                            , SUM(footballer_data.value) AS team_value
                        FROM footballer JOIN footballer_data ON footballer.id = footballer_data.id
                        WHERE footballer.league_id = %s
                        GROUP BY footballer.owner_id
                    ) AS f ON player.id = f.owner_id
                    RIGHT JOIN (
                        SELECT
                            player_id
                            , COALESCE(points, 0) AS points
                        FROM fixture_details
                        WHERE fixture_n = %s AND league_id = %s
                    ) AS fixture ON fixture.player_id = player.id
                    WHERE
                        player.league_id = %s
                        AND player.points IS NOT NULL
                        AND player.budget IS NOT NULL
                        AND player.lineup IS NOT NULL
                    ORDER BY fixture.points DESC
                    """,
                (league_id, fixture_id, league_id, league_id),
            )

        players = cursor.fetchall()

        cursor.close()
        conn.close()
        return {
            "status": "success",
            "leaderboard": players,
            "columns": ["id", "name", "points", "team_value", "picture_url"],
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "leaderboard": []}
