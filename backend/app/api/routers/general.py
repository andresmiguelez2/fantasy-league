from fastapi import APIRouter
from backend.app.db.database import pg_connect, mongo_client
from .logger import logger


router = APIRouter(prefix="/general", tags=["general"])


@router.get('/footballers_to_update')
def footballers_to_update(limit: int = 20, time_threshold: int = 30*60):
    """
    Get footballers that are either owned or on the market and haven't been updated recently.
    
    Args:
        limit (int): Maximum number of footballers to return. Default is 20.
        time_threshold (int): Time in seconds since last update to consider a footballer as needing an update. Default is 30 minutes.
    """
    conn = pg_connect()
    cursor = conn.cursor()

    cursor.execute(
        """
            SELECT
	            footballer.id
            FROM footballer JOIN footballer_data ON footballer.id = footballer_data.id
            WHERE
                (owner_id IS NOT NULL OR on_market = TRUE)
                AND EXTRACT (EPOCH FROM (NOW() - COALESCE(last_updated, '1970-01-01'))) > %s
            ORDER BY last_updated ASC
            LIMIT %s
            """,
        (time_threshold, limit)
    )

    footballer_ids = cursor.fetchall()

    return {"status": "success", "footballer_ids": [fid[0] for fid in footballer_ids], "columns": ["id"]}


@router.get('/opened_fixtures')
def get_opened_fixtures(league_id: int):
    """Get all the IDs of the fixtures that have been played in the league.

    Args:
        league_id (int): The league ID to filter by.
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT n
            FROM fixture AS fx JOIN fixture_details AS fxd ON fx.n = fxd.fixture_n
            WHERE fx.opened = True AND fxd.league_id = %s
            ORDER BY n ASC
            """
        , (league_id,))

        opened_fixtures = [row[0] for row in cursor.fetchall()]
        return {"status": "success", "opened_fixtures": opened_fixtures}
    except Exception as e:
        logger.error(f"Error retrieving opened fixtures: {e}")
        return {"status": "error", "opened_fixtures": None}