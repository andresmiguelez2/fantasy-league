import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app.api.routers.market import player_market


class PlayerMarketTests(unittest.TestCase):
    @patch("backend.app.api.routers.market.load_market")
    @patch("backend.app.api.routers.market.pg_connect")
    def test_player_market_returns_market_closing_timestamp(self, mock_pg_connect, mock_load_market):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, "Player A", 100, None, "2025-01-01 12:00:00", None, 1.2, 10, False, "FW")
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        closing_ts = datetime(2030, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_market = MagicMock()
        mock_market.closing_ts = closing_ts
        mock_load_market.return_value = mock_market

        response = player_market(player_id=1, league_id=10)

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["market_closing_timestamp"], closing_ts.isoformat())

    @patch("backend.app.api.routers.market.load_market")
    @patch("backend.app.api.routers.market.pg_connect")
    def test_player_market_returns_null_market_closing_timestamp_when_missing(self, mock_pg_connect, mock_load_market):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn
        mock_load_market.return_value = None

        response = player_market(player_id=1, league_id=10)

        self.assertEqual(response["status"], "success")
        self.assertIsNone(response["market_closing_timestamp"])


if __name__ == "__main__":
    unittest.main()
