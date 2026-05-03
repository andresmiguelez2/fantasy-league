from fastapi import APIRouter
from aux.database import pg_connect, mongo_client
from aux.constants import POSITION_ORDER, LINEUP_POSITIONS, BANK_NAME
from .logger import logger


router = APIRouter(prefix="/players", tags=["players"])


@router.get('/{player_id}')
def get_player_info(player_id: int, league_id: int):
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
            WHERE id = %s AND league_id = %s
            """,
            (player_id, league_id),
        )
        player = cursor.fetchone()

        cursor.close()
        conn.close()
        return {
            "status": "success",
            "player": player,
            "columns": ["id", "name", "budget", "points"]
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "player": None}


@router.get('/{player_id}/lineup')
def get_player_lineup(player_id: int, league_id: int):
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
            WHERE id = %s AND league_id = %s
            """,
            (player_id, league_id),
        )
        lineup = cursor.fetchone()[0]

        cursor.close()
        conn.close()
        return {
            "status": "success",
            "lineup": lineup,
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "lineup": None}


@router.get('/{player_id}/lineup/footballers')
def get_footballers_on_lineup(player_id: int, league_id: int):
    """
    Get the footballers on the player's lineup

    Args:
        player_id (int): The player ID
        league_id (int): The league ID

    API Returns:
        list[list[int]]: A list of lists containing the footballer IDs on the lineup. Includes GK, DF, MD, FW
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
                AND f.league_id = %s
            ORDER BY fd.position, f.id
            """,
            (player_id, league_id),
        )

        footballers_on_lineup = cursor.fetchall()

        lineup = [[], [], [], []]
        for id, position in footballers_on_lineup:
            lineup[POSITION_ORDER[position]].append(id)

        return {
            "status": "success",
            "lineup_footballers": lineup,
            "columns": ["GK", "DF", "MD", "FW"]
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "lineup": None}
    

@router.get('/{player_id}/fixtures/{fixture_n}/lineup')
def get_fixture_lineup(player_id: int, fixture_n: int, league_id: int):
    """
    Get the footballers on the player's lineup for a specific fixture

    Args:
        player_id (int): The player ID
        fixture_id (int): The fixture number
        league_id (int): The league ID
    
    API Returns:
        list[list[int]]: A list of lists containing the footballer IDs on the lineup. Includes GK, DF, MD, FW
        list[int]: The formation lineup
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                fx.footballer_id
                , fd.position
            FROM (
                SELECT
                    footballer_id
                FROM fixture_details
                CROSS JOIN LATERAL unnest(footballers_on_lineup) AS footballer_id
                WHERE
                    fixture_n = %s
                    AND player_id = %s
                    AND league_id = %s
            ) AS fx LEFT JOIN footballer_data AS fd ON fx.footballer_id = fd.id
            ORDER BY position, fx.footballer_id
            """,
            (fixture_n, player_id, league_id),
        )
        footballers_on_lineup = cursor.fetchall()

        cursor.execute(
            """
            SELECT lineup
            FROM fixture_details
            WHERE fixture_n = %s AND player_id = %s AND league_id = %s
            """,
            (fixture_n, player_id, league_id),
        )
        formation_result = cursor.fetchone()
        formation = formation_result[0] if formation_result else []

        cursor.close()
        conn.close()

        lineup = [[], [], [], []]
        for id, position in footballers_on_lineup:
            lineup[POSITION_ORDER[position]].append(id)

        return {
            "status": "success",
            "lineup_footballers": lineup,
            "lineup": formation,
            "columns": ["GK", "DF", "MD", "FW"]
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "lineup": [], "lineup_footballers": []}


@router.get('/{player_id}/fixtures')
def get_player_fixtures(player_id: int, league_id: int):
    """
    Get the fixtures where the player took part.
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT fixture_n
            FROM fixture_details
            WHERE player_id = %s AND league_id = %s
            ORDER BY fixture_n DESC
            """,
            (player_id, league_id),
        )

        fixtures = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return {"status": "success", "fixtures": fixtures}
    except Exception as e:
        logger.error(f"Error retrieving fixtures for player {player_id}: {e}")
        return {"status": "error", "fixtures": None}


@router.get('/{player_id}/bench')
def get_footballers_not_on_lineup(player_id: int, league_id: int, target_position: str = None):
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
                AND league_id = %s
                AND f.on_lineup = false
                AND (%s IS NULL OR fd.position = %s)
            ORDER BY fd.position, f.id
            """,
            (player_id, league_id, target_position, target_position),
        )

        footballers_on_lineup = cursor.fetchall()

        lineup = [[], [], [], []]
        for id, position in footballers_on_lineup:
            lineup[POSITION_ORDER[position]].append(id)

        if not target_position:
            return {
                "status": "success",
                "benched_footballers": lineup,
                "columns": ["GK", "DF", "MD", "FW"]
            }
        else:
            return {
                "status": "success",
                "benched_footballers": lineup[POSITION_ORDER[target_position]],
                "columns": [target_position]
            }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "lineup": None}
    

@router.get('/{player_id}/substitutes')
def get_available_substitutes(player_id: int, league_id: int, position: str):
    """Get the available substitutes for a given position
    """
    try:
        conn = pg_connect()

        try:
            position = LINEUP_POSITIONS[int(position)]
        except ValueError:
            pass

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                f.id
                , fd.name
                , fd.value
                , fd.total_points
                , fd.average_points
            FROM footballer f LEFT JOIN footballer_data fd ON f.id = fd.id
            WHERE
                f.owner_id = %s
                AND f.on_lineup = false
                AND fd.position = %s
                AND f.league_id = %s
            ORDER BY id
            """,
            (player_id, position, league_id),
        )

        substitutes = cursor.fetchall()

        cursor.close()
        conn.close()
        return {
            "status": "success",
            "substitutes": substitutes,
            "columns": ["id", "name", "value", "total_points", "average_points"]
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "substitutes": []}
    

@router.post('/{player_id}/lineup')
def update_player_lineup(player_id: int, league_id: int, lineup: list[int]):
    """Update the player lineup. This should be a list of three integers representing the number of defenders, midfielders, and forwards.
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
            WHERE id = %s AND league_id = %s
            """,
            (lineup, player_id, league_id),
        )
        conn.commit()

        validate_lineup(player_id, league_id, lineup)

        cursor.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error"}
    

def validate_lineup(player_id: int, league_id: int, lineup: list[int]):
    """
    Validate the player's lineup and remove incompatible footballers
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        # Get current footballers on lineup (from DB, not from API)
        cursor.execute(
            """
            SELECT
                f.id
                , fd.position
            FROM footballer AS f JOIN footballer_data AS fd ON f.id = fd.id
            WHERE
                f.owner_id = %s
                AND f.league_id = %s
                AND f.on_lineup = true
            ORDER BY fd.position, f.id
            """,
            (player_id, league_id),
        )

        footballers_on_lineup = cursor.fetchall()
        
        # Organize by position
        lineup_by_pos = [[], [], [], []]
        for f_id, position in footballers_on_lineup:
            lineup_by_pos[POSITION_ORDER[position]].append(f_id)

        # Identify footballers to remove
        footballers_to_remove = []
        for pos_idx, (f_list, n_spots) in enumerate(zip(lineup_by_pos, [1] + lineup)):
            if len(f_list) > n_spots:
                # Remove excess footballers from this position
                footballers_to_remove.extend(f_list[n_spots:])

        # Remove excess footballers
        for footballer_id in footballers_to_remove:
            cursor.execute(
                """
                UPDATE footballer
                SET on_lineup = FALSE
                WHERE id = %s
                """,
                (footballer_id,)
            )

        conn.commit()
        cursor.close()
        conn.close()

        if footballers_to_remove:
            logger.info(f"Footballers removed from player's {player_id} lineup due to incompatibilities: {footballers_to_remove}")
    except Exception as e:
        logger.error(f"Error validating lineup: {e}")

@router.get('/{player_id}/squad')
def get_squad(player_id: int, league_id: int):
    """Get the squad of a player.

    Args:
        player_id (int): The player ID.
        league_id (int): The league ID to filter by.
    """
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
                , fd.total_points
                , fd.average_points
                , f.on_market
                , f.on_market_since
            FROM footballer f LEFT JOIN footballer_data fd ON f.id = fd.id
            WHERE f.owner_id = %s AND f.league_id = %s
            ORDER BY id
            """,
            (player_id, league_id),
        )
        footballers = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "footballers": footballers,
            "columns": [
                "id",
                "name",
                "team",
                "value",
                "total_points",
                "average_points",
                "on_market",
                "on_market_since"
            ]
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "footballers": []}


@router.get('/{player_id}/bids/incoming')
def get_player_incoming_bids(player_id: int, league_id: int):
    """Get all incoming bids for a player's footballers.

    Args:
        player_id (int): The ID of the player to get incoming bids for.
        league_id (int): The league ID to filter by.
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                b.id AS bid_id
                , b.timestamp
                , f.id AS footballer_id
                , COALESCE(p.name, %s) AS bidder_name
                , fd.name AS footballer_name
                , b.amount
            FROM bid AS b
                LEFT JOIN footballer AS f ON b.footballer_id = f.id AND b.league_id = f.league_id
                LEFT JOIN footballer_data AS fd ON b.footballer_id = fd.id
                LEFT JOIN player AS p on b.bidder_id = p.id
            WHERE f.owner_id = %s AND b.league_id = %s
            ORDER BY footballer_id, b.timestamp DESC
            """,
            (BANK_NAME, player_id, league_id)
        )
        bids = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "bids": bids, "columns": ["bid_id", "timestamp", "footballer_id", "bidder_name", "footballer_name", "amount"]}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "bids": []}


@router.get('/{player_id}/bids/outgoing')
def get_player_outgoing_bids(player_id: int, league_id: int):
    """Get all outgoing bids made by a player.

    Args:
        player_id (int): The ID of the player to get outgoing bids for.
        league_id (int): The league ID to filter by.
    """
    try:
        conn = pg_connect()

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                b.id AS bid_id
                , b.timestamp
                , f.id AS footballer_id
                , COALESCE(p.name, %s) AS owner_name
                , fd.name AS footballer_name
                , b.amount
            FROM bid AS b
                LEFT JOIN footballer AS f ON b.footballer_id = f.id AND b.league_id = f.league_id
                LEFT JOIN footballer_data AS fd ON b.footballer_id = fd.id
                LEFT JOIN player AS p on f.owner_id = p.id
            WHERE b.bidder_id = %s AND b.league_id = %s
            ORDER BY footballer_id, b.timestamp DESC
            """,
            (BANK_NAME, player_id, league_id)
        )
        bids = cursor.fetchall()

        cursor.close()
        conn.close()
        return {"status": "success", "bids": bids, "columns": ["bid_id", "timestamp", "footballer_id", "owner_name", "footballer_name", "amount"]}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "bids": []}
