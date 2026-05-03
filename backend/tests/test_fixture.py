import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from backend.app.models.fixture import Fixture, get_current_fixture


class GetCurrentFixtureTests(unittest.TestCase):
    def _mock_connection(self, open_fixtures):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = open_fixtures

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        return mock_conn, mock_cursor

    @patch("app.classes.fixture.pg_connect")
    def test_returns_first_non_dangling_fixture(self, mock_pg_connect):
        start_ts = datetime(2025, 1, 1, 12, 0, 0)
        time_open = timedelta(days=2)

        mock_conn, mock_cursor = self._mock_connection([(1, "fixture-1", start_ts, time_open, True)])
        mock_pg_connect.return_value = mock_conn

        fixture = get_current_fixture()

        self.assertIsInstance(fixture, Fixture)
        self.assertEqual(fixture.n, "fixture-1")
        self.assertEqual(fixture.start_dt, start_ts)
        self.assertFalse(fixture.finished)

        mock_cursor.execute.assert_called_once()
        mock_cursor.fetchall.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.classes.fixture.ckeck_all_matches_finished", return_value=False)
    @patch("app.classes.fixture.pg_connect")
    def test_returns_none_when_only_dangling(self, mock_pg_connect, mock_check):
        start_ts = datetime(2025, 1, 1, 12, 0, 0)
        time_open = timedelta(days=6)

        mock_conn, _ = self._mock_connection([(1, "fixture-1", start_ts, time_open, True)])
        mock_pg_connect.return_value = mock_conn

        fixture = get_current_fixture()

        self.assertIsNone(fixture)

    @patch("app.classes.fixture.ckeck_all_matches_finished", return_value=False)
    @patch("app.classes.fixture.pg_connect")
    def test_skips_dangling_then_returns_next(self, mock_pg_connect, mock_check):
        start_ts_a = datetime(2025, 1, 1, 12, 0, 0)
        start_ts_b = datetime(2025, 1, 2, 12, 0, 0)

        open_fixtures = [
            (1, "dangling-1", start_ts_a, timedelta(days=7), True),
            (2, "fixture-2", start_ts_b, timedelta(days=1), True),
        ]

        mock_conn, _ = self._mock_connection(open_fixtures)
        mock_pg_connect.return_value = mock_conn

        fixture = get_current_fixture()

        self.assertIsInstance(fixture, Fixture)
        self.assertEqual(fixture.n, "fixture-2")
        self.assertEqual(fixture.start_dt, start_ts_b)
        self.assertFalse(fixture.finished)


if __name__ == "__main__":
    unittest.main()
