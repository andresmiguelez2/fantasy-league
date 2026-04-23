import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
from aux.database import pg_connect
from aux.auth import verify_token
from .logger import logger


router = APIRouter(prefix="/leagues", tags=["leagues"])
security = HTTPBearer()


def _ensure_league_columns():
    """Add invite_code and created_by columns to league table if they do not already exist."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                ALTER TABLE league
                ADD COLUMN IF NOT EXISTS invite_code UUID UNIQUE DEFAULT NULL
                """
            )
            cursor.execute(
                """
                ALTER TABLE league
                ADD COLUMN IF NOT EXISTS created_by INT REFERENCES users(id) DEFAULT NULL
                """
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        logger.error(f"Error ensuring league columns: {e}")


_ensure_league_columns()


def _get_user_leagues(user_id: int):
    """Get all leagues for a user."""
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


def _validate_name_field(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("Field must not be empty")
    if len(v) > 255:
        raise ValueError("Field must not exceed 255 characters")
    return v


class CreateLeagueRequest(BaseModel):
    league_name: str
    player_name: str

    @field_validator("league_name", "player_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        return _validate_name_field(v)


class JoinLeagueRequest(BaseModel):
    invite_code: str
    player_name: str

    @field_validator("player_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        return _validate_name_field(v)


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
            invite_code = str(uuid.uuid4())

            # Create the league
            cursor.execute(
                "INSERT INTO league (name, invite_code, created_by) VALUES (%s, %s, %s) RETURNING id",
                (request.league_name, invite_code, user_id),
            )
            league_id = cursor.fetchone()[0]

            # Create a player for this user in the new league (always auto-generate the player ID)
            cursor.execute(
                """
                INSERT INTO player (name, league_id, user_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (request.player_name, league_id, user_id),
            )
            player_id = cursor.fetchone()[0]

            conn.commit()
        finally:
            cursor.close()
            conn.close()

        logger.info(
            f"Created league '{request.league_name}' (ID: {league_id}) "
            f"with player '{request.player_name}' (ID: {player_id}) "
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
def get_user_leagues_query(user_id: int = Query(...)):
    """Return all leagues for the given user ID."""
    return _get_user_leagues(user_id)


@router.get("/by-invite/{invite_code}")
def get_league_by_invite_code(invite_code: str):
    """Return basic league info for a given invite code (no authentication required)."""
    try:
        uuid.UUID(invite_code)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invite code format")

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, name FROM league WHERE invite_code = %s",
                (invite_code,),
            )
            result = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        if not result:
            raise HTTPException(status_code=404, detail="League not found")

        return {"status": "success", "league": {"id": result[0], "name": result[1]}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching league by invite code: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch league")


@router.get("/{league_id}/invite")
def get_league_invite(
    league_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Return the invite code for a league. Only the league creator can access this."""
    user_id = _get_user_id_from_token(credentials)

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT l.invite_code, l.created_by
                FROM league l
                JOIN player p ON p.league_id = l.id
                WHERE l.id = %s AND p.user_id = %s
                """,
                (league_id, user_id),
            )
            result = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this league",
            )

        invite_code, created_by = result

        # Enforce creator-only access for leagues that have a known creator
        if created_by is not None and created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the league creator can share the invite link",
            )

        # Generate and persist an invite code for leagues that pre-date this feature
        if not invite_code:
            invite_code = str(uuid.uuid4())
            conn2 = pg_connect()
            cursor2 = conn2.cursor()
            try:
                cursor2.execute(
                    "UPDATE league SET invite_code = %s WHERE id = %s",
                    (invite_code, league_id),
                )
                conn2.commit()
            finally:
                cursor2.close()
                conn2.close()

        return {"status": "success", "invite_code": str(invite_code)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invite code for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invite code")


@router.post("/join")
def join_league(
    request: JoinLeagueRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Join a league using an invite code."""
    user_id = _get_user_id_from_token(credentials)

    try:
        uuid.UUID(request.invite_code)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid invite code format")

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, name FROM league WHERE invite_code = %s",
                (request.invite_code,),
            )
            league_row = cursor.fetchone()

            if not league_row:
                raise HTTPException(status_code=404, detail="Invalid invite code")

            league_id, league_name = league_row

            cursor.execute(
                "SELECT id FROM player WHERE league_id = %s AND user_id = %s",
                (league_id, user_id),
            )
            if cursor.fetchone():
                raise HTTPException(
                    status_code=409,
                    detail="You are already a member of this league",
                )

            cursor.execute(
                """
                INSERT INTO player (name, league_id, user_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (request.player_name, league_id, user_id),
            )
            player_id = cursor.fetchone()[0]

            conn.commit()
        finally:
            cursor.close()
            conn.close()

        logger.info(
            f"User {user_id} joined league '{league_name}' (ID: {league_id}) "
            f"with player '{request.player_name}' (ID: {player_id})"
        )
        return {
            "status": "success",
            "league": {"id": league_id, "name": league_name},
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining league for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to join league")
