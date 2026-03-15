"""
Database setup script for league support

This script creates the league table and adds league_id columns
to the player and fixture tables if they don't already exist.
Run this script to enable multiple-league support.
"""
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aux.database import pg_connect

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def setup_league_tables():
    """Create the league table and add league_id FKs to player and fixture tables."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        # Create the league table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS league (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("League table created (or already exists).")

        # Add league_id to the player table if it doesn't exist
        cursor.execute("""
            ALTER TABLE player
            ADD COLUMN IF NOT EXISTS league_id INTEGER REFERENCES league(id)
        """)
        logger.info("league_id column added to player table (or already exists).")

        # Add league_id to the fixture table if it doesn't exist
        cursor.execute("""
            ALTER TABLE fixture
            ADD COLUMN IF NOT EXISTS league_id INTEGER REFERENCES league(id)
        """)
        logger.info("league_id column added to fixture table (or already exists).")

        conn.commit()
        cursor.close()
        conn.close()

        return True
    except Exception as e:
        logger.error(f"Error setting up league tables: {e}")
        return False


def create_league(name: str) -> int | None:
    """Create a new league and return its id."""
    try:
        conn = pg_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO league (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
            RETURNING id
            """,
            (name,)
        )
        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        if result:
            league_id = result[0]
            logger.info(f"League '{name}' created with id {league_id}.")
            return league_id
        else:
            # Already exists – look it up
            conn = pg_connect()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM league WHERE name = %s", (name,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            if row:
                logger.info(f"League '{name}' already exists with id {row[0]}.")
                return row[0]
        return None
    except Exception as e:
        logger.error(f"Error creating league: {e}")
        return None


if __name__ == "__main__":
    logger.info("Starting league database setup...")

    if setup_league_tables():
        logger.info("✓ League table setup complete")
    else:
        logger.error("✗ Failed to create league tables")
        sys.exit(1)

    logger.info("League database setup completed successfully!")
