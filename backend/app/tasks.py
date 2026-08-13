import asyncio
import logging
import time

from backend.app.api.routers.footballer import (
    _auto_increment_release_clause,
    update_footballer_info,
)
from backend.app.api.routers.general import footballers_to_update
from backend.app.core.constants import (
    HANDLE_DANGLING_FIXTURES_INTERVAL,
    LOOP_TIME_BUFFER,
    LOOP_TIME_SECONDS,
    N_REQUEST_BUFFER,
    UPDATE_DB_INTERVAL,
    UPDATE_FIXTURES_INTERVAL,
)
from backend.app.models.fixture import get_current_fixture, update_fixture_times
from backend.app.models.league import get_leagues
from backend.app.models.market import Market, load_last_market, load_market

logger = logging.getLogger(__name__)


def _cache_data(start_time: float, leagues: list[int]) -> None:
    target_footballers = footballers_to_update(time_threshold=UPDATE_DB_INTERVAL)["footballer_ids"]

    if time.time() - start_time > LOOP_TIME_SECONDS - LOOP_TIME_BUFFER:
        logger.info("No time to cache data into database this loop.")
        return

    for fid in target_footballers:
        elapsed_time = update_footballer_info(fid).get('elapsed_time')
        elapsed_time += _auto_increment_release_clause(fid, leagues)
        if time.time() - start_time > LOOP_TIME_SECONDS - elapsed_time * N_REQUEST_BUFFER:
            break


def _update_data(n_iteration: int) -> None:
    if n_iteration % UPDATE_FIXTURES_INTERVAL == 0:
        update_fixture_times()


def _run_iteration(active_markets: dict[int, Market | None], n_iteration: int, start_time: float) -> None:
    """Run a single iteration of the background loop (blocking).

    ``active_markets`` is a dict keyed by league_id so that leagues added
    after startup are automatically included on the next iteration.
    """
    leagues = get_leagues()

    for league_id in leagues:
        market = active_markets.get(league_id)
        if market:
            market.fulfill_market()

        active_markets[league_id] = load_market(league_id)

        if not active_markets[league_id]:
            last_market = load_last_market(league_id)
            if last_market:
                last_market.fulfill_market()
            active_markets[league_id] = last_market

    active_fixture = get_current_fixture(
        handle_dangling=n_iteration % HANDLE_DANGLING_FIXTURES_INTERVAL == 0
    )
    if active_fixture:
        active_fixture.fulfill_fixture()

    _cache_data(start_time, leagues)
    _update_data(n_iteration)


async def background_loop() -> None:
    """Async background loop that replaces the blocking while-True loop.

    Runs market fulfillment, fixture processing and data caching on every
    iteration using a thread-pool executor so that blocking I/O does not stall
    the FastAPI event loop. The inter-iteration delay is handled with
    ``asyncio.sleep`` instead of a busy-wait.
    """
    logger.info("Background task started.")

    active_markets: dict[int, Market | None] = {}
    n_iteration = 0

    while True:
        try:
            start_time = time.time()
            await asyncio.to_thread(
                _run_iteration, active_markets, n_iteration, start_time
            )
            elapsed = time.time() - start_time
            await asyncio.sleep(max(0.0, LOOP_TIME_SECONDS - elapsed))
            n_iteration += 1
        except asyncio.CancelledError:
            logger.info("Background task stopped.")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in background loop: {e}")
            await asyncio.sleep(10)
