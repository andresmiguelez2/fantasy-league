from fastapi import APIRouter
from aux.database import pg_connect
from .logger import logger
from typing import Optional


router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get('/{fixture_id}')
def leaderboard(fixture_id: str, league_id: Optional[int] = None):
    """Get the leaderboard of players, optionally filtered by league.

    Args:
        fixture_id (str): The fixture number or "total" for overall standings.
        league_id (int, optional): Filter results to players belonging to this league.
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        team_value_subquery = """
            (
                SELECT
                    footballer.owner_id
                    , SUM(footballer_data.value) AS team_value
                FROM footballer JOIN footballer_data ON footballer.id = footballer_data.id
                GROUP BY footballer.owner_id
            ) AS f
        """

        league_filter = "WHERE player.league_id = %s" if league_id is not None else ""

        if fixture_id == "total":
            query = f"""
                SELECT
                    player.id
                    , player.name
                    , player.points
                    , f.team_value
                FROM player
                LEFT JOIN {team_value_subquery} ON player.id = f.owner_id
                {league_filter}
                ORDER BY points DESC
            """
            params = (league_id,) if league_id is not None else ()
        else:
            query = f"""
                SELECT
                    player.id
                    , player.name
                    , fixture.points
                    , f.team_value
                FROM player
                LEFT JOIN {team_value_subquery} ON player.id = f.owner_id
                RIGHT JOIN (
                    SELECT
                        player_id
                        , COALESCE(points, 0) AS points
                    FROM fixture_details
                    WHERE fixture_n = %s
                ) AS fixture ON fixture.player_id = player.id
                {league_filter}
                ORDER BY points DESC
            """
            params = (fixture_id, league_id) if league_id is not None else (fixture_id,)

        cursor.execute(query, params)
        players = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "leaderboard": players, "columns": ["id", "name", "points", "team_value"]}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "leaderboard": []}