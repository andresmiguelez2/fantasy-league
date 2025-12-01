from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from aux.constants import POSITION_ORDER
from .footballer import get_footballer_image
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


@router.get('/lineup/{player_id}')
def get_player_lineup(player_id: int):
    """Get the player lineup
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                lineup
            FROM player
            WHERE id = %s
            """,
            (player_id,),
        )
        lineup = cursor.fetchone()[0]

        cursor.close()
        conn.close()
        return {"status": "success", "lineup": lineup}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "lineup": None}

@router.get('/lineup_footballers/{player_id}')
def get_footballers_on_lineup(player_id: int):
    """
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                f.id
                , fd.position
            FROM footballer AS f JOIN footballer_data AS fd ON f.id = fd.id
            WHERE
                f.owner_id = %s
                AND f.on_lineup = true
            ORDER BY fd.position, f.id
            """,
            (player_id,),
        )

        footballers_on_lineup = cursor.fetchall()

        lineup = [[], [], [], []]
        for id, position in footballers_on_lineup:
            # image = get_footballer_image(id)
            lineup[POSITION_ORDER[position]].append(id)

        return {"status": "success", "lineup_footballers": lineup}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "lineup": None}
    

@router.post('/update/lineup/{player_id}')
def update_player_lineup(player_id: int, lineup: list[int]):
    """Update the player lineup
    """
    assert len(lineup) == 3, logger.error("Lineup must contain exactly 3 elements: [DF, MD, FW]")
    assert all(isinstance(x, int) for x in lineup), logger.error("All elements in lineup must be integers")
    assert all(0 <= x <= 10 for x in lineup), logger.error("All elements in lineup must be between 0 and 10")
    assert sum(lineup) == 10, logger.error("The sum of the lineup elements must be 10")

    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE player
            SET lineup = %s
            WHERE id = %s
            """,
            (lineup, player_id),
        )
        conn.commit()

        cursor.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error"}