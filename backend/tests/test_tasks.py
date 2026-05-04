import asyncio
import sys
import os
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class BackgroundLoopTests(unittest.IsolatedAsyncioTestCase):
    @patch("backend.app.tasks.get_leagues", return_value=[1])
    @patch("backend.app.tasks.load_market", return_value=None)
    @patch("backend.app.tasks.load_last_market")
    @patch("backend.app.tasks.get_current_fixture", return_value=None)
    @patch("backend.app.tasks.footballers_to_update", return_value={"footballer_ids": []})
    @patch("backend.app.tasks.update_fixture_times")
    async def test_background_loop_runs_and_cancels(
        self,
        mock_update_fixture_times,
        mock_footballers_to_update,
        mock_get_current_fixture,
        mock_load_last_market,
        mock_load_market,
        mock_get_leagues,
    ):
        """background_loop should run at least one iteration and stop cleanly when cancelled."""
        from backend.app.tasks import background_loop

        mock_market = MagicMock()
        mock_load_last_market.return_value = mock_market

        task = asyncio.create_task(background_loop())
        # Give the loop time to start and execute at least one iteration.
        await asyncio.sleep(0.1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        # At least one iteration should have executed market + fixture logic.
        mock_load_last_market.assert_called()
        mock_market.fulfill_market.assert_called()
        mock_get_current_fixture.assert_called()

    @patch("backend.app.tasks.get_leagues", return_value=[1, 2])
    @patch("backend.app.tasks.load_market")
    @patch("backend.app.tasks.load_last_market")
    @patch("backend.app.tasks.get_current_fixture", return_value=None)
    @patch("backend.app.tasks.footballers_to_update", return_value={"footballer_ids": []})
    @patch("backend.app.tasks.update_fixture_times")
    async def test_active_markets_dict_is_updated_per_league(
        self,
        mock_update_fixture_times,
        mock_footballers_to_update,
        mock_get_current_fixture,
        mock_load_last_market,
        mock_load_market,
        mock_get_leagues,
    ):
        """active_markets dict should be updated for each league on every iteration."""
        from backend.app.tasks import background_loop

        market_a = MagicMock()
        market_b = MagicMock()
        mock_load_market.side_effect = [market_a, market_b]

        task = asyncio.create_task(background_loop())
        await asyncio.sleep(0.1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        # load_market should have been called once per league.
        self.assertEqual(mock_load_market.call_count, 2)

    @patch("backend.app.tasks.get_leagues", return_value=[1])
    @patch("backend.app.tasks.load_market", return_value=None)
    @patch("backend.app.tasks.load_last_market")
    @patch("backend.app.tasks.get_current_fixture")
    @patch("backend.app.tasks.footballers_to_update", return_value={"footballer_ids": []})
    @patch("backend.app.tasks.update_fixture_times")
    async def test_fixture_fulfill_called_when_active(
        self,
        mock_update_fixture_times,
        mock_footballers_to_update,
        mock_get_current_fixture,
        mock_load_last_market,
        mock_load_market,
        mock_get_leagues,
    ):
        """fulfill_fixture should be called when an active fixture exists."""
        from backend.app.tasks import background_loop

        mock_fixture = MagicMock()
        mock_get_current_fixture.return_value = mock_fixture
        mock_load_last_market.return_value = MagicMock()

        task = asyncio.create_task(background_loop())
        await asyncio.sleep(0.1)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        mock_fixture.fulfill_fixture.assert_called()

    @patch("backend.app.tasks.get_leagues", return_value=[1])
    @patch("backend.app.tasks.load_market", side_effect=RuntimeError("db error"))
    @patch("backend.app.tasks.get_current_fixture", return_value=None)
    @patch("backend.app.tasks.footballers_to_update", return_value={"footballer_ids": []})
    @patch("backend.app.tasks.update_fixture_times")
    async def test_loop_recovers_from_exception(
        self,
        mock_update_fixture_times,
        mock_footballers_to_update,
        mock_get_current_fixture,
        mock_load_market,
        mock_get_leagues,
    ):
        """An unexpected exception should not kill the loop; it should retry after a sleep."""
        from backend.app.tasks import background_loop

        task = asyncio.create_task(background_loop())
        # Allow the error-recovery sleep to begin.
        await asyncio.sleep(0.05)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

        # load_market raised an error; the loop should have attempted at least once.
        mock_load_market.assert_called()


if __name__ == "__main__":
    unittest.main()
