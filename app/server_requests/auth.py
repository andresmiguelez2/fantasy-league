from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from aux.auth import authenticate_user, create_access_token, verify_token, get_user_by_id
from aux.database import pg_connect
from .logger import logger

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


class LeagueEntry(BaseModel):
    league_id: int
    league_name: str
    player_id: int


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    id: int
    player_id: int
    username: str
    leagues: List[LeagueEntry]


class UserInfo(BaseModel):
    id: int
    username: str
    player_id: int
    leagues: List[LeagueEntry]


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Authenticate user and return JWT token together with the list of leagues
    the user participates in.
    """
    user = authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user["id"]), "username": user["username"], "player_id": user["player_id"]}
    )
    
    logger.info(f"User {user['username']} logged in successfully")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": user["id"],
        "player_id": user["player_id"],
        "username": user["username"],
        "leagues": user.get("leagues", []),
    }


def get_current_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to get current user from JWT token
    Can be used to protect routes
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = int(payload.get("sub"))
    user = get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Logout endpoint (token invalidation handled client-side)
    """
    # In a JWT system, logout is typically handled client-side by removing the token
    # For more advanced implementations, you could maintain a token blacklist
    logger.info("User logged out")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserInfo)
def get_current_user(current_user: dict = Depends(get_current_user_from_token)):
    """
    Get current authenticated user information, including leagues they participate in.
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ul.league_id, l.name, ul.player_id
            FROM user_leagues ul
            JOIN league l ON ul.league_id = l.id
            WHERE ul.user_id = %s
            ORDER BY l.name
            """,
            (current_user["id"],),
        )
        leagues = [
            {"league_id": row[0], "league_name": row[1], "player_id": row[2]}
            for row in cursor.fetchall()
        ]
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error fetching leagues for /me: {e}")
        leagues = []

    return {**current_user, "leagues": leagues}
