import logging
import time
from classes.market import load_market, load_last_market
from aux.constants import LOOP_TIME_SECONDS, SLEEP_TIME, LOOP_TIME_BUFFER, N_REQUEST_BUFFER, UPDATE_DB_INTERVAL, HANDLE_DANGLING_FIXTURES_INTERVAL, UPDATE_FIXTURES_INTERVAL
from server_requests.server_requests import server_app
from server_requests.footballer import update_footballer_info
from server_requests.general import footballers_to_update
from classes.fixture import get_current_fixture, update_fixture_times
from classes.league import get_leagues


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s \t %(name)s \t %(levelname)s \t %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def cache_data(start_time):
    target_footballers = footballers_to_update(time_threshold=UPDATE_DB_INTERVAL)["footballer_ids"]

    if time.time() - start_time > LOOP_TIME_SECONDS - LOOP_TIME_BUFFER:
        logger.info("No time to cache data into database this loop.")
        return

    for fid in target_footballers:
        elapsed_time = update_footballer_info(fid)['elapsed_time']
        if time.time() - start_time > LOOP_TIME_SECONDS - elapsed_time*N_REQUEST_BUFFER:
            break


def update_data(n_iteration):
    if n_iteration%UPDATE_FIXTURES_INTERVAL == 0:
        update_fixture_times()


def wait_loop_time(start_time):
    """Check if the loop time has exceeded the defined limit."""
    while True:
        if time.time() - start_time < LOOP_TIME_SECONDS:
            time.sleep(SLEEP_TIME)
        else:
            return


if __name__ == "__main__":
    logger.info("Backend app is starting...")
    
    leagues = get_leagues()
    active_markets = [None] * len(leagues)
    n_iteration = 0

    while True:
        try:
            start_time = time.time()

            for i, league_id in enumerate(leagues):
                if active_markets[i]:
                    active_markets[i].fulfill_market()

                active_markets[i] = load_market(league_id)

                if not active_markets[i]:
                    active_markets[i] = load_last_market(league_id)
                    active_markets[i].fulfill_market()

            active_fixture = get_current_fixture(handle_dangling=n_iteration%HANDLE_DANGLING_FIXTURES_INTERVAL==0)
            if active_fixture:
                active_fixture.fulfill_fixture()
            
            cache_data(start_time)
            wait_loop_time(start_time)
            update_data(n_iteration)
            
            n_iteration += 1
        except KeyboardInterrupt:
            print("\n")
            logger.info("Backend app stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            time.sleep(10)
