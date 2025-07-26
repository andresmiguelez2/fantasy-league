import os
import logging
import time
import psycopg2
from market import Market


LOOP_TIME_SECONDS = 10


# Configure logging to output to stdout (container logs)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def wait_loop_time(start_time):
    """Check if the loop time has exceeded the defined limit."""
    while True:
        if time.time() - start_time < LOOP_TIME_SECONDS:
            time.sleep(0.001)
        else:
            return


def load_market():
    try:
        logger.info("Connecting to database...")
        # Connect to PostgreSQL database using environment variables
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "postgres_db"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432"),
        )

        cursor = conn.cursor()

        logger.info("Executing market query...")
        # Example query to load market data
        cursor.execute(
            """
            SELECT *
            FROM market
            WHERE closing_timestamp > now()
        """
        )
        market_data = cursor.fetchall()

        if len(market_data) > 1:
            logger.error("Several concurrent markets found in the database.")
            raise ValueError("Several concurrent markets found in the database.")
        if len(market_data) == 0:
            logger.warning("No active market found in the database.")
            raise ValueError("No active market found in the database.")

        market = Market()
        market.id = market_data[0][0]
        market.closing_ts = market_data[0][1]
        market.has_been_closed = market_data[0][2]
        logger.info(f"Found market {market}")

        cursor.close()
        conn.close()
        logger.info("Database connection closed successfully")

        return market

    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        return []


if __name__ == "__main__":
    logger.info("Backend app is starting...")

    while True:
        try:
            start_time = time.time()

            logger.info("Loading market data...")
            active_market = load_market()
            logger.info("Market loading completed")

            wait_loop_time(start_time)

        except KeyboardInterrupt:
            print("\n")
            logger.info("Application interrupted by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(10)
