"""
Database setup script for the multi-league fantasy app.

Creates the following tables if they don't already exist:
  - users           (authentication)
  - league          (league registry)
  - user_leagues    (maps users to their per-league player record)

Also ensures the player table has a league_id column.

Run this script before starting the application for the first time, or
after upgrading to the multi-league schema.
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


def create_league_table():
    """Create the league table if it doesn't exist."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS league (
                id   SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            )
        """)

        conn.commit()
        logger.info("league table ensured.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error creating league table: {e}")
        return False


def add_league_id_to_player():
    """Add league_id column to the player table if it doesn't already exist."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute("""
            ALTER TABLE player
            ADD COLUMN IF NOT EXISTS league_id INTEGER REFERENCES league(id)
        """)

        conn.commit()
        logger.info("player.league_id column ensured.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error adding league_id to player: {e}")
        return False


def create_user_leagues_table():
    """Create the user_leagues junction table if it doesn't exist."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_leagues (
                user_id   INTEGER NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
                league_id INTEGER NOT NULL REFERENCES league(id) ON DELETE CASCADE,
                player_id INTEGER          REFERENCES player(id),
                PRIMARY KEY (user_id, league_id)
            )
        """)

        conn.commit()
        logger.info("user_leagues table ensured.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error creating user_leagues table: {e}")
        return False


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


def create_league(name: str) -> int | None:
    """Create a new league and return its id."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO league (name) VALUES (%s) RETURNING id",
            (name,),
        )
        league_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"League created: {name!r} (ID: {league_id})")
        return league_id
    except Exception as e:
        logger.error(f"Error creating league: {e}")
        return None


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


def add_user_to_league(user_id: int, league_id: int, player_id: int) -> bool:
    """Add a user to a league with their per-league player record.

    Args:
        user_id:   ID of the row in the ``users`` table.
        league_id: ID of the row in the ``league`` table.
        player_id: ID of the row in the ``player`` table that represents
                   this user's participation in the given league.
    """
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO user_leagues (user_id, league_id, player_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, league_id) DO UPDATE
                SET player_id = EXCLUDED.player_id
            """,
            (user_id, league_id, player_id),
        )

        # Keep player.league_id consistent
        cursor.execute(
            "UPDATE player SET league_id = %s WHERE id = %s",
            (league_id, player_id),
        )

        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"User {user_id} added to league {league_id} as player {player_id}")
        return True
    except Exception as e:
        logger.error(f"Error adding user to league: {e}")
        return False


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

    # Create league table
    if create_league_table():
        logger.info("✓ League table setup complete")
    else:
        logger.error("✗ Failed to create league table")
        sys.exit(1)

    # Add league_id to player
    if add_league_id_to_player():
        logger.info("✓ player.league_id column ensured")
    else:
        logger.error("✗ Failed to add league_id to player")
        sys.exit(1)

    # Create user_leagues table
    if create_user_leagues_table():
        logger.info("✓ user_leagues table setup complete")
    else:
        logger.error("✗ Failed to create user_leagues table")
        sys.exit(1)
    
    # Optionally migrate users from file
    logger.info("Attempting to migrate users from file...")
    migrate_users_from_file()
    
    logger.info("Database setup completed successfully!")

