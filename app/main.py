import logging
import time
from market import load_market


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


if __name__ == "__main__":
    logger.info("Backend app is starting...")

    while True:
        try:
            start_time = time.time()

            logger.info("Loading market data...")
            active_market = load_market(logger)
            logger.info("Market loading completed")

            wait_loop_time(start_time)

        except KeyboardInterrupt:
            print("\n")
            logger.info("Backend app stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(10)
