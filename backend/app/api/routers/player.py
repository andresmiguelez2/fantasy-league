import imghdr

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
from backend.app.db.database import pg_connect, mongo_client
from backend.app.core.constants import POSITION_ORDER, LINEUP_POSITIONS
from backend.app.core.auth import verify_token
from .footballer import get_footballer_image, set_footballer_on_lineup
from .logger import logger


router = APIRouter(prefix="/player", tags=["player"])
security = HTTPBearer()


def _get_user_id_from_token(credentials: HTTPAuthorizationCredentials) -> int:
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return int(payload.get("sub"))


class UpdatePlayerProfileRequest(BaseModel):
    name: str | None = None
    picture_url: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        if len(v) > 255:
            raise ValueError("name must not exceed 255 characters")
        return v

    @field_validator("picture_url")
    @classmethod
    def validate_picture_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("picture_url must not be empty")
        if len(v) > 2048:
            raise ValueError("picture_url must not exceed 2048 characters")
        return v


@router.patch("/profile/{player_id}")
def update_player_profile(
    player_id: int,
    request: UpdatePlayerProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Update the name and/or picture for a specific player (must belong to authenticated user)."""
    user_id = _get_user_id_from_token(credentials)

    if request.name is None and request.picture_url is None:
        raise HTTPException(status_code=400, detail="name or picture_url must be provided")

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            # Verify ownership
            cursor.execute(
                "SELECT id FROM player WHERE id = %s AND user_id = %s",
                (player_id, user_id),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="Not authorized to update this player")

            if request.name is not None:
                cursor.execute(
                    "UPDATE player SET name = %s WHERE id = %s AND user_id = %s",
                    (request.name, player_id, user_id),
                )
            if request.picture_url is not None:
                cursor.execute(
                    "UPDATE player SET picture_url = %s WHERE id = %s AND user_id = %s",
                    (request.picture_url, player_id, user_id),
                )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update player profile")


@router.get("/profile-picture/{user_id}")
def get_player_profile_picture(user_id: int):
    """Return the player's profile picture as raw bytes from MongoDB."""
    try:
        client = mongo_client()
        db = client["FantasyMDB"]

        doc = db.player_picture.find_one({"user_id": user_id})
        if doc is None:
            client.close()
            raise HTTPException(status_code=404, detail="No profile picture found.")

        img_field = doc.get("image_binary")
        if img_field is None:
            client.close()
            raise HTTPException(status_code=404, detail="No profile picture found.")

        img_bytes = bytes(img_field)
        fmt = imghdr.what(None, img_bytes)
        content_type = f"image/{fmt}" if fmt else "application/octet-stream"

        client.close()
        return Response(content=img_bytes, media_type=content_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving profile picture for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile picture")


@router.post("/profile-picture")
def upload_player_profile_picture(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Upload a profile picture for the authenticated user. Stores the image in MongoDB
    and updates picture_url for all of the user's player rows in Postgres."""
    user_id = _get_user_id_from_token(credentials)

    try:
        img_bytes = file.file.read()
        if not img_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Store in MongoDB (upsert so only one picture per user)
        client = mongo_client()
        db = client["FantasyMDB"]
        db.player_picture.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "image_binary": img_bytes}},
            upsert=True,
        )
        client.close()

        # Update picture_url for all of this user's players to the backend endpoint
        picture_url = f"/player/profile-picture/{user_id}"
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE player SET picture_url = %s WHERE user_id = %s",
                (picture_url, user_id),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        return {"status": "success", "picture_url": picture_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading profile picture for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload profile picture")


@router.get("/picture/{player_id}")
def get_league_player_picture(player_id: int):
    """Return the per-league picture for a specific player row as raw bytes from MongoDB."""
    try:
        client = mongo_client()
        db = client["FantasyMDB"]

        doc = db.league_player_picture.find_one({"player_id": player_id})
        if doc is None:
            client.close()
            raise HTTPException(status_code=404, detail="No picture found for this league.")

        img_field = doc.get("image_binary")
        if img_field is None:
            client.close()
            raise HTTPException(status_code=404, detail="No picture found for this league.")

        img_bytes = bytes(img_field)
        fmt = imghdr.what(None, img_bytes)
        content_type = f"image/{fmt}" if fmt else "application/octet-stream"

        client.close()
        return Response(content=img_bytes, media_type=content_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving league picture for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve league picture")


@router.post("/{player_id}/picture")
def upload_league_player_picture(
    player_id: int,
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Upload a picture for a single league membership (player row).

    Stores the image in MongoDB keyed by player_id and updates picture_url only
    for that player row, leaving the user's other leagues untouched."""
    user_id = _get_user_id_from_token(credentials)

    try:
        img_bytes = file.file.read()
        if not img_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        conn = pg_connect()
        cursor = conn.cursor()
        try:
            # Verify ownership of the player row
            cursor.execute(
                "SELECT id FROM player WHERE id = %s AND user_id = %s",
                (player_id, user_id),
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="Not authorized to update this player")

            # Store in MongoDB (upsert so only one picture per league membership)
            client = mongo_client()
            db = client["FantasyMDB"]
            db.league_player_picture.update_one(
                {"player_id": player_id},
                {"$set": {"player_id": player_id, "image_binary": img_bytes}},
                upsert=True,
            )
            client.close()

            # Point only this player row at its own picture
            picture_url = f"/player/picture/{player_id}"
            cursor.execute(
                "UPDATE player SET picture_url = %s WHERE id = %s AND user_id = %s",
                (picture_url, player_id, user_id),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        return {"status": "success", "picture_url": picture_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading league picture for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload league picture")


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


@router.get('/lineup/{player_id}')
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


@router.get('/lineup_footballers/{player_id}')
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
    

@router.get('/fixture_lineup/{player_id}')
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


@router.get('/fixtures/{player_id}')
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


@router.get('/benched_footballers/{player_id}')
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
    

@router.get('/available_subs/{player_id}')
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
    

@router.post('/update/lineup/{player_id}')
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


@router.get("/bid_sum/{player_id}")
def get_player_bid_sum(player_id: int, league_id: int):
    """Get the total sum of active bids made by a player in a specific league.
    
    Args:
        player_id (int): The ID of the player to get the bid sum for.
        league_id (int): The league ID to filter by.
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM bid
            WHERE
                active = true
                AND league_id = %s
                AND bidder_id = %s
            """,
            (league_id, player_id)
        )
        total_bid_sum = cursor.fetchone()[0]

        cursor.close()
        conn.close()
        return {"status": "success", "total_bid_sum": total_bid_sum}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"status": "error", "total_bid_sum": 0}


def get_team_value(player_id: int, league_id: int) -> int:
    """Get the total value of a player's team in a specific league.

    Args:
        player_id (int): The ID of the player to get the team value for.
        league_id (int): The league ID to filter by.

    Returns:
        int: The total value of the player's team.
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                COALESCE(SUM(footballer_data.value), 0)
            FROM footballer JOIN footballer_data ON footballer.id = footballer_data.id
            WHERE
                footballer.league_id = %s
                AND footballer.owner_id = %s
            """,
            (league_id, player_id)
        )
        team_value = int(cursor.fetchone()[0])

        cursor.close()
        conn.close()
        return team_value
    except Exception as e:
        logger.error(f"Error: {e}")
        return 0