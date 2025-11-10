from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from .logger import logger
from pydantic import BaseModel


router = APIRouter(prefix="/squad", tags=["squad"])


@router.get("/{player_id}")
def squad(player_id: int):
    """Get the squad of a player."""
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                f.id
                , fd.name
                , fd.team
                , fd.value
                , f.on_market
                , f.on_market_since
            FROM footballer f LEFT JOIN footballer_data fd ON f.id = fd.id
            WHERE f.owner_id = %s
            ORDER BY id
            """,
            (player_id,),
        )
        players = cursor.fetchall()
        cursor.close()
        conn.close()

        return {"players": players}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"players": []}
    

class MarketFootballer(BaseModel):
    footballer_id: int
    player_id: int
    on_market: bool

@router.post("/edit_player")
def edit_player_status(market_footballer: MarketFootballer):
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        on_market_since = 'now()' if market_footballer.on_market else None

        cursor.execute(
            """
            UPDATE footballer
            SET 
                on_market = %s
                , on_market_since = %s
            WHERE id = %s and owner_id = %s;
            """,
            (market_footballer.on_market, on_market_since, market_footballer.footballer_id, market_footballer.player_id)
        )
        affected = cursor.rowcount

        if affected == 0:
            logger.warning(f"Player {market_footballer.player_id} not found or not owned by user.")
            msg = {"status": "error", "message": "Player not found or not owned by user."}
        else:
            logger.info(f"Player {market_footballer.player_id} {'placed on' if market_footballer.on_market else 'removed from'} market")
            msg = {"status": "success", "message": "Player status updated successfully."}

        conn.commit()
        cursor.close()
        conn.close()
        
        return msg
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}