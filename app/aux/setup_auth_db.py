"""
Database setup script for users table and league tables

This script creates the users table and league tables if they don't exist.
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


def create_user(username: str, password: str):
    """Create a new user"""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        
        password_hash = get_password_hash(password)
        
        cursor.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (%s, %s)
            RETURNING id
            """,
            (username, password_hash)
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


def create_league(league_name: str):
    """Create a new league"""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO league (name)
            VALUES (%s)
            RETURNING id
            """,
            (league_name,)
        )
        
        league_id = cursor.fetchone()[0]

        cursor.execute(
            '''
            INSERT INTO footballer (url_name, on_market, on_lineup, league_id)
            SELECT DISTINCT
                url_name
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
            VALUES (now() + INTERVAL '1 day', %s)
            """, 
            (league_id,)
        )

        conn.commit()
        
        logger.info(f"League and market created successfully: {league_name} (ID: {league_id})")
        
        cursor.close()
        conn.close()
        
        return league_id
    except Exception as e:
        logger.error(f"Error creating league: {e}")
        return None
    

def create_player(name: str, league_id: int, user_id: int, player_id: int):
    """Create a new player"""
    try:
        conn = pg_connect()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO player (name, id, league_id, user_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (name, player_id, league_id, user_id)
        )
        
        player_id = cursor.fetchone()[0]
        conn.commit()
        
        logger.info("Player created successfully")
        
        cursor.close()
        conn.close()
        
        return player_id
    except Exception as e:
        logger.error(f"Error creating player: {e}")
        return None


def migrate_users_from_file():
    """
    Migrate users from the /secrets/users.env file to the database
    Format: username:password
    """
    try:
        with open("/secrets/users.env", "r") as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                parts = line.split(':', 1)
                if len(parts) != 2:
                    logger.warning("Skipping malformed line in users.env")
                    continue
                username, password = parts[0].strip(), parts[1].strip()
                if not username or not password:
                    logger.warning("Skipping line with empty username or password")
                    continue

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
                    create_user(username, password)

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
    logger.info("Attempting to migrate users from file...")
    migrate_users_from_file()
    
    logger.info("Database setup completed successfully!")
