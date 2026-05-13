import re

import psycopg2.errors
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
from typing import Optional
from backend.app.core.auth import authenticate_user, create_access_token, verify_token, get_user_by_id, get_password_hash
from backend.app.db.database import pg_connect
from .logger import logger

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")
_USERNAME_MIN_LEN = 3
_USERNAME_MAX_LEN = 30


def _ensure_username_unique_index():
    """Create a case-insensitive unique index on users.username if it does not exist."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS users_username_lower_idx
                ON users (LOWER(username))
                """
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        logger.error(f"Error ensuring username unique index: {e}")


_ensure_username_unique_index()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < _USERNAME_MIN_LEN:
            raise ValueError(f"Username must be at least {_USERNAME_MIN_LEN} characters long")
        if len(v) > _USERNAME_MAX_LEN:
            raise ValueError(f"Username must be at most {_USERNAME_MAX_LEN} characters long")
        if not _USERNAME_RE.match(v):
            raise ValueError("Username may only contain letters, digits, and underscores")
        return v


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    id: int
    username: str


class UserInfo(BaseModel):
    id: int
    username: str


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Authenticate user and return JWT token
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
        data={"sub": str(user["id"]), "username": user["username"]}
    )
    
    logger.info(f"User {user['username']} logged in successfully")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "id": user["id"],
        "username": user["username"]
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    """
    Register a new user account
    """
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 6 characters long",
        )

    conn = None
    cursor = None
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        # Check if username already exists (case-insensitive)
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(%s)", (request.username,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

        password_hash = get_password_hash(request.password)

        cursor.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
            RETURNING id
            """,
            (request.username, password_hash),
        )
        user_id = cursor.fetchone()[0]
        conn.commit()

        logger.info(f"New user registered: {request.username} (ID: {user_id})")

        return {"id": user_id, "username": request.username}
    except HTTPException:
        raise
    except psycopg2.errors.UniqueViolation:
        # DB-level unique index caught a concurrent duplicate registration
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user",
        )
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


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
    Get current authenticated user information
    """
    return current_user
