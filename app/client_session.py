import logging
import time
from classes.player import Session
from aux.constants import LOOP_TIME_SECONDS, SLEEP_TIME


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
            time.sleep(SLEEP_TIME)
        else:
            return


if __name__ == "__main__":
    logger.info("Client app is starting...")
    active_market = None

    while True:
        session = Session()
        if session.login():
            logger.info(f"User {session.user} logged in successfully as player_id {session.player_id}.")
            break
        else:
            logger.warning("Login failed.")
            continue

    while True:
        try:
            start_time = time.time()
            
            if session.active:
                session.main_menu()
            else:
                logger.warning("Session is not active. Exiting.")
                break

            # wait_loop_time(start_time)

        except KeyboardInterrupt:
            print("\n")
            session.logout()
            logger.info("Client app stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(LOOP_TIME_SECONDS)
