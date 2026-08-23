import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.app.api.routers.player import get_player_bid_sum


class PlayerRouterTests(unittest.TestCase):
    @patch("backend.app.api.routers.player.pg_connect")
    def test_get_player_bid_sum_filters_by_league_then_bidder(self, mock_pg_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (250,)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        response = get_player_bid_sum(player_id=7, league_id=3)

        self.assertEqual(response, {"status": "success", "total_bid_sum": 250})
        self.assertEqual(mock_cursor.execute.call_args.args[1], (3, 7))


if __name__ == "__main__":
    unittest.main()
