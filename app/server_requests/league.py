from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
from aux.database import pg_connect
from aux.auth import verify_token
from .player import get_player_id
from .logger import logger


router = APIRouter(prefix="/leagues", tags=["leagues"])
security = HTTPBearer()


def _get_player_leagues(player_id: int):
    """Get all leagues for a specific player ID."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT league.id, league.name
                FROM league RIGHT JOIN player on player.league_id = league.id
                WHERE player.id = %s
                ORDER BY id
                """, (player_id,)
            )
            leagues = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
        return {
            "status": "success",
            "leagues": [{"id": row[0], "name": row[1]} for row in leagues],
        }
    except Exception as e:
        logger.error(f"Error retrieving leagues: {e}")
        return {"status": "error", "leagues": []}


def _get_user_leagues(user_id: int):
    """Get all leagues for a user via the user_players join table."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    league.id
                    , league.name
                FROM league
                JOIN player ON player.league_id = league.id
                JOIN users ON users.id = player.user_id
                WHERE users.id = %s
                ORDER BY league.id
                """, (user_id,)
            )
            leagues = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
        return {
            "status": "success",
            "leagues": [{"id": row[0], "name": row[1]} for row in leagues],
        }
    except Exception as e:
        logger.error(f"Error retrieving leagues for user {user_id}: {e}")
        return {"status": "error", "leagues": []}


def _get_user_id_from_token(credentials: HTTPAuthorizationCredentials) -> int:
    """Validate JWT token and return the user ID, raising 401 on failure."""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return int(payload.get("sub"))


class CreateLeagueRequest(BaseModel):
    league_name: str
    player_name: str

    @field_validator("league_name", "player_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field must not be empty")
        if len(v) > 255:
            raise ValueError("Field must not exceed 255 characters")
        return v


@router.post("")
def create_league(
    request: CreateLeagueRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Create a new league and a player entry for the authenticated user."""
    user_id = _get_user_id_from_token(credentials)

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            # Create the league
            cursor.execute(
                "INSERT INTO league (name) VALUES (%s) RETURNING id",
                (request.league_name,),
            )
            league_id = cursor.fetchone()[0]

            # get player_id
            player_id = get_player_id(user_id)

            # Create a player for this user in the new league
            if player_id is not None:
                cursor.execute(
                    """
                    INSERT INTO player (name, league_id, user_id, id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (request.player_name, league_id, user_id, player_id),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO player (name, league_id, user_id)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    (request.player_name, league_id, user_id),
                )

            conn.commit()
        finally:
            cursor.close()
            conn.close()

        logger.info(
            f"Created league '{request.league_name}' (ID: {league_id}) "
            f"with player '{request.player_name}' (ID: {player_id})"
            f"for user {user_id}"
        )
        return {
            "status": "success",
            "league": {"id": league_id, "name": request.league_name},
        }
    except Exception as e:
        logger.error(f"Error creating league for user {user_id}: {e}")
        return {"status": "error", "detail": "Failed to create league. The league name may already be taken."}


@router.get("/player-names")
def get_player_names(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Return the distinct player names previously used by the authenticated user."""
    user_id = _get_user_id_from_token(credentials)

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT DISTINCT p.name
                FROM player p
                JOIN users u ON p.user_id = u.id
                WHERE u.id = %s
                ORDER BY p.name
                """,
                (user_id,),
            )
            names = [row[0] for row in cursor.fetchall()]
        finally:
            cursor.close()
            conn.close()
        return {"status": "success", "names": names}
    except Exception as e:
        logger.error(f"Error retrieving player names for user {user_id}: {e}")
        return {"status": "error", "names": []}


@router.get("/active-player")
def get_active_player_for_league(
    league_id: int = Query(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Return the player_id for the authenticated user in a specific league."""
    user_id = _get_user_id_from_token(credentials)

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT p.id
                FROM player p
                JOIN league l ON p.league_id = l.id
                WHERE p.user_id = %s AND l.id = %s
                """,
                (user_id, league_id),
            )
            result = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        if not result:
            return {
                "status": "error",
                "detail": "Player not found for this user and league",
            }

        return {
            "status": "success",
            "player_id": result[0],
        }
    except Exception as e:
        logger.error(
            f"Error retrieving active player for user {user_id}, league {league_id}: {e}"
        )
        return {
            "status": "error",
            "detail": "Failed to retrieve active player",
        }


@router.get("")
def get_player_leagues_query(
    player_id: int = Query(None), user_id: int = Query(None)
):
    if user_id is not None:
        return _get_user_leagues(user_id)
    if player_id is not None:
        return _get_player_leagues(player_id)
    return {"status": "error", "leagues": [], "detail": "Must provide player_id or user_id"}


@router.get("/{player_id}")
def get_player_leagues(player_id: int):
    return _get_player_leagues(player_id)
