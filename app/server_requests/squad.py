from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from .logger import logger
from pydantic import BaseModel


router = APIRouter(prefix="/squads", tags=["squad"])


@router.get("/{player_id}")
def squad(player_id: int):
    """Get the squad of a player."""
    try:
        conn = pg_connect()

        client = mongo_client()
        db = client["FantasyMDB"]

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id
                , name
                , on_market
                , on_market_since
            FROM footballer WHERE owner_id = %s ORDER BY id
            """,
            (player_id,),
        )
        players = cursor.fetchall()
        cursor.close()
        conn.close()

        player_data = list()
        for player in players:
            value = db.footballer.find({"id": player[0]})[0]['market_details'][-1]['value']
            team = db.footballer.find({"id": player[0]})[0]['team']
            player_data.append((player[0], player[1], team, value, player[2], player[3]))

        return {"players": player_data}
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