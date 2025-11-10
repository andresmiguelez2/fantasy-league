import logging
import time
from classes.market import load_market, load_last_market
from aux.constants import LOOP_TIME_SECONDS, SLEEP_TIME
from server_requests.server_requests import server_app


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
            time.sleep(SLEEP_TIME)
        else:
            return


if __name__ == "__main__":
    logger.info("Backend app is starting...")
    active_market = None

    while True:
        try:
            start_time = time.time()

            if active_market:
                active_market.fulfill_market()

            active_market = load_market()
            if not active_market:
                active_market = load_last_market()
                active_market.fulfill_market()

            wait_loop_time(start_time)

        except KeyboardInterrupt:
            print("\n")
            logger.info("Backend app stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(10)
