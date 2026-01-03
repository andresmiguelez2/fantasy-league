"""
Database setup script for users table

This script creates the users table if it doesn't exist.
Run this script before using the authentication system.
"""
import logging
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aux.database import pg_connect
from aux.auth import get_password_hash

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def create_users_table():
    """Create the users table if it doesn't exist"""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                player_id INTEGER REFERENCES player(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("Users table created successfully")
        
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error creating users table: {e}")
        return False


def create_user(username: str, password: str, player_id: int):
    """Create a new user"""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        
        password_hash = get_password_hash(password)
        
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, player_id)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (username, password_hash, player_id)
        )
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        
        logger.info(f"User created successfully: {username} (ID: {user_id})")
        
        cursor.close()
        conn.close()
        
        return user_id
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None


def migrate_users_from_file():
    """
    Migrate users from the /secrets/users.env file to the database
    Format: username:password:player_id
    """
    try:
        with open("/secrets/users.env", "r") as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    username, password, player_id = line.split(':')
                    username = username.strip()
                    password = password.strip()
                    player_id = int(player_id.strip())
                    
                    # Check if user already exists
                    conn = pg_connect()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                    existing = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    if existing:
                        logger.info(f"User {username} already exists, skipping")
                    else:
                        create_user(username, password, player_id)
        
        logger.info("User migration completed")
        return True
    except FileNotFoundError:
        logger.warning("User secrets file not found at /secrets/users.env")
        logger.info("You can manually create users using the create_user function")
        return False
    except Exception as e:
        logger.error(f"Error migrating users: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting database setup...")
    
    # Create users table
    if create_users_table():
        logger.info("✓ Users table setup complete")
    else:
        logger.error("✗ Failed to create users table")
        sys.exit(1)
    
    # Optionally migrate users from file
    logger.info("Attempting to migrate users from file...")
    migrate_users_from_file()
    
    logger.info("Database setup completed successfully!")
