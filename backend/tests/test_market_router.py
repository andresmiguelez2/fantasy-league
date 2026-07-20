import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app.api.routers.market import (
    BidRequest,
    _player_has_enough_budget,
    get_player_future_bids,
    get_player_incoming_bids,
    get_player_outgoing_bids,
    place_bid,
    player_market,
    reply_to_bid,
)


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

    @patch("backend.app.api.routers.market.load_market")
    @patch("backend.app.api.routers.market.pg_connect")
    def test_player_market_only_joins_active_bids_available_now(self, mock_pg_connect, mock_load_market):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn
        mock_load_market.return_value = None

        player_market(player_id=1, league_id=10)

        query = mock_cursor.execute.call_args_list[0].args[0]
        self.assertIn("timestamp <= now()", query)

    @patch("backend.app.api.routers.market.pg_connect")
    def test_outgoing_bids_only_returns_active_bids_available_now(self, mock_pg_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        response = get_player_outgoing_bids(player_id=1, league_id=10)

        self.assertEqual(response["status"], "success")
        query = mock_cursor.execute.call_args.args[0]
        self.assertIn("b.active = TRUE", query)
        self.assertIn("b.timestamp <= now()", query)

    @patch("backend.app.api.routers.market.pg_connect")
    def test_incoming_bids_only_returns_active_bids_available_now(self, mock_pg_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        response = get_player_incoming_bids(player_id=1, league_id=10)

        self.assertEqual(response["status"], "success")
        query = mock_cursor.execute.call_args.args[0]
        self.assertIn("b.active = TRUE", query)
        self.assertIn("b.timestamp <= now()", query)

    @patch("backend.app.api.routers.market.pg_connect")
    def test_future_bids_only_returns_future_active_bids(self, mock_pg_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        response = get_player_future_bids(player_id=1, league_id=10)

        self.assertEqual(response["status"], "success")
        query = mock_cursor.execute.call_args.args[0]
        self.assertIn("b.timestamp > now()", query)

    @patch("backend.app.api.routers.market.get_team_value", return_value=1000000)
    @patch("backend.app.api.routers.market.get_player_info", return_value={"player": [1, "Player", 1000000]})
    @patch("backend.app.api.routers.market.get_player_bid_sum", return_value={"total_bid_sum": 0})
    @patch("backend.app.api.routers.market.Footballer")
    @patch("backend.app.api.routers.market.pg_connect")
    def test_place_bid_uses_requested_future_timestamp(
        self,
        mock_pg_connect,
        mock_footballer,
        _mock_bid_sum,
        _mock_player_info,
        _mock_team_value,
    ):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [("Full Name", "url-name", None), None]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        footballer_instance = MagicMock()
        footballer_instance.data = {"market_details": [{"value": 100}]}
        mock_footballer.return_value = footballer_instance

        future_timestamp = datetime(2030, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        response = place_bid(
            BidRequest(
                player_id=1,
                footballer_id=2,
                bid_amount=150,
                league_id=10,
                timestamp=future_timestamp,
            )
        )

        self.assertEqual(response["status"], "success")
        insert_call = mock_cursor.execute.call_args_list[2]
        self.assertEqual(insert_call.args[1], (2, 1, 150, future_timestamp, 10))

    @patch("backend.app.api.routers.market.get_team_value", return_value=200)
    @patch("backend.app.api.routers.market.get_player_info", return_value={"player": [1, "Player", 100]})
    @patch("backend.app.api.routers.market.get_player_bid_sum", return_value={"total_bid_sum": 100})
    def test_player_has_enough_budget_allows_replacing_existing_bid_without_double_counting(
        self,
        _mock_bid_sum,
        _mock_player_info,
        _mock_team_value,
    ):
        has_enough_budget, budget_error = _player_has_enough_budget(
            player_id=1,
            league_id=10,
            new_bid_amount=130,
            current_bid_amount=100,
        )

        self.assertTrue(has_enough_budget)
        self.assertIsNone(budget_error)

    @patch("backend.app.api.routers.market.get_team_value", return_value=200)
    @patch("backend.app.api.routers.market.get_player_info", return_value={"player": [1, "Player", 100]})
    @patch("backend.app.api.routers.market.get_player_bid_sum", return_value={"total_bid_sum": 150})
    def test_player_has_enough_budget_allows_removing_existing_bid(
        self,
        _mock_bid_sum,
        _mock_player_info,
        _mock_team_value,
    ):
        has_enough_budget, budget_error = _player_has_enough_budget(
            player_id=1,
            league_id=10,
            new_bid_amount=0,
            current_bid_amount=60,
        )

        self.assertTrue(has_enough_budget)
        self.assertIsNone(budget_error)

    @patch("backend.app.api.routers.market.get_team_value", return_value=1000000)
    @patch("backend.app.api.routers.market.get_player_info", return_value={"player": [1, "Player", 1000000]})
    @patch("backend.app.api.routers.market.get_player_bid_sum", return_value={"total_bid_sum": 100})
    @patch("backend.app.api.routers.market.Footballer")
    @patch("backend.app.api.routers.market.pg_connect")
    def test_place_bid_updates_existing_bid_instead_of_deleting_and_reinserting(
        self,
        mock_pg_connect,
        mock_footballer,
        _mock_bid_sum,
        _mock_player_info,
        _mock_team_value,
    ):
        mock_cursor = MagicMock()
        future_timestamp = datetime(2030, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_cursor.fetchone.side_effect = [
            ("Full Name", "url-name", None),
            (9, 100),
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        footballer_instance = MagicMock()
        footballer_instance.data = {"market_details": [{"value": 100}]}
        mock_footballer.return_value = footballer_instance

        response = place_bid(
            BidRequest(
                player_id=1,
                footballer_id=2,
                bid_amount=150,
                league_id=10,
                timestamp=future_timestamp,
            )
        )

        self.assertEqual(response["status"], "success")
        update_call = mock_cursor.execute.call_args_list[2]
        self.assertIn("UPDATE bid", update_call.args[0])
        self.assertEqual(update_call.args[1], (150, future_timestamp, 9))
        executed_sql = " ".join(call.args[0] for call in mock_cursor.execute.call_args_list)
        self.assertNotIn("DELETE FROM bid", executed_sql)
        self.assertNotIn("INSERT INTO bid", executed_sql)

    @patch("backend.app.api.routers.market.get_team_value", return_value=1000000)
    @patch("backend.app.api.routers.market.get_player_info", return_value={"player": [1, "Player", 1000000]})
    @patch("backend.app.api.routers.market.get_player_bid_sum", return_value={"total_bid_sum": 100})
    @patch("backend.app.api.routers.market.Footballer")
    @patch("backend.app.api.routers.market.pg_connect")
    def test_place_bid_updates_requested_bid_id_for_future_bid_edits(
        self,
        mock_pg_connect,
        mock_footballer,
        _mock_bid_sum,
        _mock_player_info,
        _mock_team_value,
    ):
        mock_cursor = MagicMock()
        future_timestamp = datetime(2030, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_cursor.fetchone.side_effect = [
            ("Full Name", "url-name", None),
            (5, 100),
        ]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        footballer_instance = MagicMock()
        footballer_instance.data = {"market_details": [{"value": 100}]}
        mock_footballer.return_value = footballer_instance

        response = place_bid(
            BidRequest(
                player_id=1,
                footballer_id=2,
                bid_amount=150,
                league_id=10,
                bid_id=5,
                timestamp=future_timestamp,
            )
        )

        self.assertEqual(response["status"], "success")
        lookup_call = mock_cursor.execute.call_args_list[1]
        self.assertIn("WHERE", lookup_call.args[0])
        self.assertIn("id = %s", lookup_call.args[0])
        self.assertEqual(lookup_call.args[1], (5, 2, 1, 10))
        update_call = mock_cursor.execute.call_args_list[2]
        self.assertEqual(update_call.args[1], (150, future_timestamp, 5))

    @patch("backend.app.api.routers.market.debit_player_value")
    @patch("backend.app.api.routers.market.get_team_value", return_value=100)
    @patch("backend.app.api.routers.market.get_player_info", return_value={"player": [2, "Bidder", 100]})
    @patch("backend.app.api.routers.market.get_player_bid_sum", return_value={"total_bid_sum": 150})
    @patch("backend.app.api.routers.market.pg_connect")
    def test_reply_to_bid_rejects_acceptance_when_bidder_exceeds_budget_limit(
        self,
        mock_pg_connect,
        _mock_bid_sum,
        _mock_player_info,
        _mock_team_value,
        mock_debit_player_value,
    ):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (9, 2, 80, 4)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        response = reply_to_bid(bid_id=1, league_id=10, accept=True)

        self.assertEqual(response["status"], "error")
        self.assertIn("greater debt", response["message"])
        self.assertEqual(len(mock_cursor.execute.call_args_list), 1)
        mock_debit_player_value.assert_not_called()


if __name__ == "__main__":
    unittest.main()
