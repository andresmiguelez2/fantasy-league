import sys
import os
import unittest
from unittest.mock import MagicMock, call, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app.models.market import Market


class AssignBidsTests(unittest.TestCase):
    def _make_cursor(self, bid_data):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = bid_data
        return mock_cursor

    def test_assigns_footballer_and_debits_bidder_budget(self):
        """When a bid is won, the footballer's owner_id is updated and the bidder's budget is debited."""
        bid_data = [(10, 42, 1000, None)]  # footballer_id=10, bidder_id=42, amount=1000, seller_id=None
        cursor = self._make_cursor(bid_data)

        market = Market()
        market.league_id = 7
        market._assign_bids(cursor)

        execute_calls = cursor.execute.call_args_list
        # First call: SELECT bids query
        # Second call: UPDATE footballer + DELETE bid
        # Third call: UPDATE player budget
        sql_strings = [str(c) for c in execute_calls]
        update_footballer_call = any("UPDATE footballer" in s and "owner_id" in s for s in sql_strings)
        update_budget_call = any("UPDATE player" in s and "budget" in s for s in sql_strings)

        self.assertTrue(update_footballer_call, "Should update footballer owner_id")
        self.assertTrue(update_budget_call, "Should debit bidder budget")

        # Verify the budget update uses the correct bidder_id and amount
        budget_call = next(
            c for c in execute_calls if "UPDATE player" in str(c) and "budget" in str(c)
        )
        args = budget_call.args[1]  # second positional arg to execute() is the params tuple
        self.assertEqual(args, (1000, 42, 7))

    def test_no_budget_update_when_bidder_is_none(self):
        """When the bidder_id is NULL (league bid), no budget update should happen."""
        bid_data = [(10, None, 500, None)]  # bidder_id is None
        cursor = self._make_cursor(bid_data)

        market = Market()
        market.league_id = 7
        market._assign_bids(cursor)

        execute_calls = cursor.execute.call_args_list
        budget_calls = [c for c in execute_calls if "UPDATE player" in str(c) and "budget" in str(c)]
        self.assertEqual(len(budget_calls), 0, "Should not update budget when bidder_id is None")

    def test_highest_bid_wins_and_gets_debited(self):
        """The highest bid wins and the winner's budget is debited."""
        bid_data = [
            (10, 42, 1500, None),  # highest bid first (sorted by amount DESC)
            (10, 99, 1000, None),  # lower bid
        ]
        cursor = self._make_cursor(bid_data)

        market = Market()
        market.league_id = 7
        market._assign_bids(cursor)

        execute_calls = cursor.execute.call_args_list
        budget_call = next(
            (c for c in execute_calls if "UPDATE player" in str(c) and "budget" in str(c)),
            None
        )
        self.assertIsNotNone(budget_call, "Should update budget for winner")
        args = budget_call.args[1]  # second positional arg to execute() is the params tuple
        self.assertEqual(args, (1500, 42, 7), "Should debit the winning bidder (42) with the winning amount (1500)")

    def test_assigns_footballer_and_credits_seller_budget(self):
        """When an owned footballer is sold, seller budget is credited."""
        bid_data = [(10, 42, 1000, 9)]  # footballer_id=10, bidder_id=42, amount=1000, seller_id=9
        cursor = self._make_cursor(bid_data)

        market = Market()
        market.league_id = 7
        market._assign_bids(cursor)

        execute_calls = cursor.execute.call_args_list
        credit_call = next(
            (c for c in execute_calls if "UPDATE player" in str(c) and "budget = budget + %s" in str(c)),
            None
        )
        self.assertIsNotNone(credit_call, "Should credit seller budget")
        args = credit_call.args[1]
        self.assertEqual(args, (1000, 9, 7), "Should credit seller (9) with sold amount (1000)")


if __name__ == "__main__":
    unittest.main()
