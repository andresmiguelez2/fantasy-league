"""
Authentication module for JWT token handling and password management
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from aux.database import pg_connect

logger = logging.getLogger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user with username and password
    Returns user info if successful, None otherwise
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        
        # Query user from database
        cursor.execute(
            """
            SELECT id, username, password_hash, player_id
            FROM users
            WHERE username = %s
            """,
            (username,)
        )
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            logger.warning(f"User not found: {username}")
            return None
        
        user_id, db_username, password_hash, player_id = user
        
        # Verify password
        if not verify_password(password, password_hash):
            logger.warning(f"Invalid password for user: {username}")
            return None
        
        return {
            "id": user_id,
            "username": db_username,
            "player_id": player_id
        }
        
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Get user information by user ID"""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, username, player_id
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )
        
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return None
        
        user_id, username, player_id = user
        return {
            "id": user_id,
            "username": username,
            "player_id": player_id
        }
        
    except Exception as e:
        logger.error(f"Error getting user by ID: {e}")
        return None
