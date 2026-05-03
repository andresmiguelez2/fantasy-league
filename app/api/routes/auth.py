from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from core.security import authenticate_user, create_access_token, verify_token, get_user_by_id, get_password_hash
from db.session import pg_connect
from core.logging import logger
from api.deps import get_current_user_from_token

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str


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

        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (request.username,))
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
