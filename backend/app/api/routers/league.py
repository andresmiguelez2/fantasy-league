import random
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
from backend.app.api.routers.footballer import update_footballer_info
from backend.app.utils.setup_auth_db import create_user
from backend.app.db.database import pg_connect
from backend.app.core.auth import verify_token
from backend.app.core.constants import (
    INITIAL_PLAYER_BUDGET,
    INITIAL_SQUAD_GK,
    INITIAL_SQUAD_DF,
    INITIAL_SQUAD_MD,
    INITIAL_SQUAD_FW,
    INITIAL_SQUAD_TOTAL_VALUE_LIMIT,
    INITIAL_SQUAD_PLAYER_VALUE_LIMIT,
    INITIAL_SQUAD_TOTAL_VALUE_TOLERANCE,
    UPDATE_DB_INTERVAL,
)
from .logger import logger


router = APIRouter(prefix="/leagues", tags=["leagues"])
security = HTTPBearer()


def _assign_initial_squad(cursor, player_id: int, league_id: int) -> list[int]:
    """Assign initial footballers to a new player in a league.

    Selects footballers randomly by position (GK, DF, MD, FW) subject to:
    - Individual value ≤ INITIAL_SQUAD_PLAYER_VALUE_LIMIT
    - Combined total value within ±INITIAL_SQUAD_TOTAL_VALUE_TOLERANCE of
      INITIAL_SQUAD_TOTAL_VALUE_LIMIT (i.e. [90 M, 100 M] with default settings)

    The algorithm:
    1. Fetches all eligible candidates per position (sorted by value DESC).
    2. Randomly draws the required number per position.
    3. If total > upper limit: replaces picks with cheapest alternatives.
    4. If total < lower bound: greedily upgrades the cheapest current picks with
       the most expensive available alternatives that still respect the upper limit.

    Returns the list of footballer IDs assigned.
    """
    upper_limit = INITIAL_SQUAD_TOTAL_VALUE_LIMIT
    lower_bound = round(upper_limit * (1 - INITIAL_SQUAD_TOTAL_VALUE_TOLERANCE))

    position_counts = [
        ('GK', INITIAL_SQUAD_GK),
        ('DF', INITIAL_SQUAD_DF),
        ('MD', INITIAL_SQUAD_MD),
        ('FW', INITIAL_SQUAD_FW),
    ]

    # Step 1: Fetch all eligible candidates per position (value DESC for upgrade step)
    all_candidates: list[tuple[str, int, list]] = []
    for position, count in position_counts:
        cursor.execute(
            """
            SELECT f.id, fd.value
            FROM footballer f
            JOIN footballer_data fd ON f.id = fd.id
            WHERE f.league_id = %s
              AND f.owner_id IS NULL
              AND fd.position = %s
              AND fd.value <= %s
            ORDER BY fd.value DESC
            """,
            (league_id, position, INITIAL_SQUAD_PLAYER_VALUE_LIMIT),
        )
        all_candidates.append((position, count, cursor.fetchall()))

    # Step 2: Random initial selection (shuffle the fetched list per position)
    selected_per_position: list[list[tuple]] = []
    for _position, count, candidates in all_candidates:
        shuffled = list(candidates)
        random.shuffle(shuffled)
        selected_per_position.append(shuffled[:count])

    total_value = sum(v for pos in selected_per_position for _, v in pos)

    # Step 3: If total exceeds upper limit, downgrade to cheapest available players
    if total_value > upper_limit:
        selected_per_position = []
        remaining = upper_limit
        for _position, count, candidates in all_candidates:
            cheapest = sorted(candidates, key=lambda x: x[1])
            chosen: list[tuple] = []
            for f_id, val in cheapest:
                if len(chosen) >= count:
                    break
                if val <= remaining:
                    chosen.append((f_id, val))
                    remaining -= val
            selected_per_position.append(chosen)
        total_value = sum(v for pos in selected_per_position for _, v in pos)

    # Step 4: If total is below lower bound, greedily upgrade cheapest picks
    if total_value < lower_bound:
        for pos_idx, (_position, _count, candidates) in enumerate(all_candidates):
            if total_value >= lower_bound:
                break
            current = selected_per_position[pos_idx]
            current_ids = {f_id for f_id, _ in current}
            # Upgrade pool: unselected candidates for this position, most expensive first
            upgrades = sorted(
                [(f_id, val) for f_id, val in candidates if f_id not in current_ids],
                key=lambda x: x[1],
                reverse=True,
            )
            used_upgrade_ids: set[int] = set()
            # Replace cheapest current players with the priciest affordable upgrades
            current_by_val = sorted(enumerate(current), key=lambda x: x[1][1])
            for orig_idx, (old_id, old_val) in current_by_val:
                if total_value >= lower_bound:
                    break
                for new_id, new_val in upgrades:
                    if new_id in used_upgrade_ids:
                        continue
                    new_total = total_value - old_val + new_val
                    if new_total <= upper_limit:
                        current[orig_idx] = (new_id, new_val)
                        used_upgrade_ids.add(new_id)
                        total_value = new_total
                        break
            selected_per_position[pos_idx] = current

        if total_value < lower_bound:
            logger.warning(
                f"Could only reach squad value {total_value:,} for player {player_id} "
                f"in league {league_id} (target lower bound: {lower_bound:,})"
            )

    # Collect all selected IDs and warn about missing slots
    selected_ids: list[int] = []
    for pos_idx, (position, count, _) in enumerate(all_candidates):
        chosen = selected_per_position[pos_idx]
        if len(chosen) < count:
            logger.warning(
                f"Could only assign {len(chosen)}/{count} {position} footballers "
                f"to player {player_id} in league {league_id}"
            )
        selected_ids.extend(f_id for f_id, _ in chosen)

    if selected_ids:
        for footballer_id in selected_ids:
            update_footballer_info(footballer_id, UPDATE_DB_INTERVAL)

        cursor.execute(
            """
            UPDATE footballer
            SET owner_id = %s
            WHERE id = ANY(%s) AND league_id = %s
            """,
            (player_id, selected_ids, league_id),
        )
        logger.info(
            f"Assigned {len(selected_ids)} initial footballers "
            f"(total value: {total_value:,}) to player {player_id} in league {league_id}"
        )

    return selected_ids


def _bid_for_initial_footballers(cursor, player_id: int, league_id: int, league_player_id: int):
    cursor.execute('''
        SELECT f.id, fd.value
        FROM footballer AS f JOIN footballer_data AS fd on f.id = fd.id
        WHERE league_id = %s AND owner_id = %s
        ''', 
        (league_id, player_id))

    footballers = cursor.fetchall()

    for footballer_id, value in footballers:
        cursor.execute('''
            INSERT INTO bid (amount, timestamp, bidder_id, footballer_id, league_id, active)
            VALUES (%s, now(), %s, %s, %s, true)
            ''', 
            (value, league_player_id, footballer_id, league_id))


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


def _create_league_impl(
    league_name: str,
    player_name: str,
    user_id: int,
) -> dict:
    """Actual league-creation logic. Callable from anywhere in source code
    without going through the API/auth layer."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            invite_code = str(uuid.uuid4())

            cursor.execute(
                "INSERT INTO league (name, invite_code, created_by) VALUES (%s, %s, %s) RETURNING id",
                (league_name, invite_code, user_id),
            )
            league_id = cursor.fetchone()[0]

            cursor.execute(
                '''
                INSERT INTO footballer (id, url_name, on_market, on_lineup, league_id)
                SELECT DISTINCT
                    id
                    , url_name
                    , false
                    , false
                    , %s
                FROM footballer
                ''',
                (league_id,)
            )

            cursor.execute(
                """
                INSERT INTO market (closing_timestamp, league_id)
                VALUES (now() + INTERVAL '-1 second', %s)
                """,
                (league_id,)
            )

            league_user_id = create_user(
                f'league_user_{league_id}',
                ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=20)),
                cursor=cursor,
            )
            cursor.execute(
                """
                INSERT INTO player (name, league_id, user_id, budget, lineup, points)
                VALUES ('League', %s, %s, NULL, NULL, NULL)
                RETURNING id
                """,
                (league_id, league_user_id),
            )
            league_player_id = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO player (name, league_id, user_id, budget)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (player_name, league_id, user_id, INITIAL_PLAYER_BUDGET),
            )
            player_id = cursor.fetchone()[0]

            _assign_initial_squad(cursor, player_id, league_id)
            _bid_for_initial_footballers(cursor, player_id, league_id, league_player_id)

            conn.commit()
        finally:
            cursor.close()
            conn.close()

        logger.info(
            f"Created league '{league_name}' (ID: {league_id}) "
            f"with player '{player_name}' (ID: {player_id}) "
            f"for user {user_id}"
        )
        return {
            "status": "success",
            "league": {"id": league_id, "name": league_name},
        }
    except Exception as e:
        logger.error(f"Error creating league for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create league. The league name may already be taken.")


@router.post("")
def create_league(
    request: CreateLeagueRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Create a new league and a player entry for the authenticated user."""
    user_id = _get_user_id_from_token(credentials)
    return _create_league_impl(request.league_name, request.player_name, user_id)

class UpdatePlayerPictureAllRequest(BaseModel):
    picture_url: str

    @field_validator("picture_url")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("picture_url must not be empty")
        if len(v) > 2048:
            raise ValueError("picture_url must not exceed 2048 characters")
        return v


@router.get("/my-profiles")
def get_my_profiles(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Return all player profiles (name, picture) for the authenticated user, one per league."""
    user_id = _get_user_id_from_token(credentials)

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT
                    p.id,
                    p.name,
                    p.picture_url,
                    l.id,
                    l.name
                FROM player p
                JOIN league l ON p.league_id = l.id
                WHERE p.user_id = %s
                ORDER BY l.id
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

        profiles = [
            {
                "player_id": row[0],
                "player_name": row[1],
                "picture_url": row[2],
                "league_id": row[3],
                "league_name": row[4],
            }
            for row in rows
        ]
        return {"status": "success", "profiles": profiles}
    except Exception as e:
        logger.error(f"Error retrieving profiles for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profiles")


@router.patch("/player-picture")
def update_all_player_pictures(
    request: UpdatePlayerPictureAllRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Update the picture_url for all players belonging to the authenticated user."""
    user_id = _get_user_id_from_token(credentials)

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE player
                SET picture_url = %s
                WHERE user_id = %s
                """,
                (request.picture_url, user_id),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error updating picture for all players of user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update picture")


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
                cursor.execute(
                    "UPDATE league SET invite_code = %s WHERE id = %s",
                    (invite_code, league_id),
                )
                conn.commit()
        finally:
            cursor.close()
            conn.close()

        return {"status": "success", "invite_code": str(invite_code)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invite code for league {league_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch invite code")


@router.delete("/{league_id}")
def delete_league(
    league_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Delete a league and all associated data. Only the league creator can do this."""
    user_id = _get_user_id_from_token(credentials)

    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            # Verify the league exists and the requester is the creator
            cursor.execute(
                "SELECT created_by FROM league WHERE id = %s",
                (league_id,),
            )
            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="League not found")

            created_by = result[0]
            if created_by != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the league creator can delete this league",
                )

            # Delete in dependency order to avoid FK constraint violations
            cursor.execute("DELETE FROM bid WHERE league_id = %s", (league_id,))
            cursor.execute("DELETE FROM fixture_details WHERE league_id = %s", (league_id,))
            cursor.execute("DELETE FROM footballer WHERE league_id = %s", (league_id,))
            cursor.execute("DELETE FROM player WHERE league_id = %s", (league_id,))
            cursor.execute("DELETE FROM users WHERE username = %s", (f'league_user_{league_id}',))
            cursor.execute("DELETE FROM market WHERE league_id = %s", (league_id,))
            cursor.execute("DELETE FROM league WHERE id = %s", (league_id,))

            conn.commit()
        finally:
            cursor.close()
            conn.close()

        logger.info(f"League {league_id} deleted by user {user_id}")
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting league {league_id} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete league")


def get_league_player_id(cursor, league_id: int) -> int:
    """Get the player ID for the 'League' user in a given league."""
    cursor.execute(
        """SELECT id 
        FROM player
        WHERE
            league_id = %s
            -- AND name = 'League'
            AND budget IS NULL
            AND points IS NULL
            AND lineup IS NULL
        """,
        (league_id,),
    )
    result = cursor.fetchone()
    if not result:
        raise ValueError(f"No 'League' player found for league {league_id}")
    return result[0]


def _join_league_impl(
    invite_code: str,
    player_name: str,
    user_id: int,
) -> dict:
    """Actual join-league logic. Callable from anywhere in source code
    without going through the API/auth layer."""
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
            league_row = cursor.fetchone()

            if not league_row:
                raise HTTPException(status_code=404, detail="Invalid invite code")

            league_id, league_name = league_row

            cursor.execute(
                "SELECT id FROM player WHERE league_id = %s AND user_id = %s",
                (league_id, user_id),
            )
            if cursor.fetchone():
                # Already a member — return the league info so the caller can navigate there
                return {
                    "status": "success",
                    "league": {"id": league_id, "name": league_name},
                    "already_member": True,
                }

            cursor.execute(
                """
                INSERT INTO player (name, league_id, user_id, budget)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (player_name, league_id, user_id, INITIAL_PLAYER_BUDGET),
            )
            player_id = cursor.fetchone()[0]

            _assign_initial_squad(cursor, player_id, league_id)
            league_player_id = get_league_player_id(cursor, league_id)
            _bid_for_initial_footballers(cursor, player_id, league_id, league_player_id)

            conn.commit()
        finally:
            cursor.close()
            conn.close()

        logger.info(
            f"User {user_id} joined league '{league_name}' (ID: {league_id}) "
            f"with player '{player_name}' (ID: {player_id})"
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


@router.post("/join")
def join_league(
    request: JoinLeagueRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Join a league using an invite code."""
    user_id = _get_user_id_from_token(credentials)
    return _join_league_impl(request.invite_code, request.player_name, user_id)