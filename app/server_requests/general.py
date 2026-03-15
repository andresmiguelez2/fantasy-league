from fastapi import APIRouter
from typing import Optional
from aux.database import pg_connect, mongo_client
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
def get_opened_fixtures(league_id: Optional[int] = None):
    """Get all the IDs of the fixtures that have been played in the league
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        if league_id is not None:
            cursor.execute(
                """
                SELECT n
                FROM FIXTURE
                WHERE opened = True AND league_id = %s
                ORDER BY n ASC
                """,
                (league_id,)
            )
        else:
            cursor.execute(
                """
                SELECT n
                FROM FIXTURE
                WHERE opened = True
                ORDER BY n ASC
                """
            )

        opened_fixtures = [row[0] for row in cursor.fetchall()]
        return {"status": "success", "opened_fixtures": opened_fixtures}
    except Exception as e:
        logger.error(f"Error retrieving opened fixtures: {e}")
        return {"status": "error", "opened_fixtures": None}


@router.get('/leagues')
def get_leagues():
    """Get all available leagues.
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name
            FROM league
            ORDER BY id ASC
            """
        )
        leagues = cursor.fetchall()
        cursor.close()
        conn.close()
        return {
            "status": "success",
            "leagues": [{"id": str(row[0]), "name": row[1]} for row in leagues],
            "columns": ["id", "name"]
        }
    except Exception as e:
        logger.error(f"Error retrieving leagues: {e}")
        return {"status": "error", "leagues": []}