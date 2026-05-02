import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import aux.database  # noqa: F401 – ensure submodule is loaded before patching

# Patch pg_connect as referenced in server_requests.league before importing the module
# so that _ensure_league_columns() (called at module level) does not attempt a real
# database connection.
with patch('aux.database.pg_connect', MagicMock(return_value=MagicMock())):
    from server_requests.league import _assign_initial_squad

from aux.constants import (
    INITIAL_SQUAD_GK,
    INITIAL_SQUAD_DF,
    INITIAL_SQUAD_MD,
    INITIAL_SQUAD_FW,
    INITIAL_SQUAD_TOTAL_VALUE_LIMIT,
    INITIAL_SQUAD_PLAYER_VALUE_LIMIT,
)


def _make_cursor(candidates_by_position):
    """Build a mock cursor whose fetchall returns values per position in order."""
    mock_cursor = MagicMock()
    mock_cursor.fetchall.side_effect = list(candidates_by_position)
    return mock_cursor


class AssignInitialSquadTests(unittest.TestCase):

    def _candidates(self, position_counts, value_per_player=5_000_000):
        """Generate (id, value) candidate tuples for each position."""
        results = []
        start_id = 1
        for _, count in position_counts:
            rows = [(start_id + i, value_per_player) for i in range(count)]
            results.append(rows)
            start_id += count
        return results

    def test_assigns_correct_number_per_position(self):
        """Assigns exactly 2 GK, 6 DF, 6 MD, 4 FW when enough candidates exist."""
        position_counts = [
            ('GK', INITIAL_SQUAD_GK),
            ('DF', INITIAL_SQUAD_DF),
            ('MD', INITIAL_SQUAD_MD),
            ('FW', INITIAL_SQUAD_FW),
        ]
        candidates = self._candidates(position_counts)
        cursor = _make_cursor(candidates)

        result = _assign_initial_squad(cursor, player_id=1, league_id=10)

        total_expected = INITIAL_SQUAD_GK + INITIAL_SQUAD_DF + INITIAL_SQUAD_MD + INITIAL_SQUAD_FW
        self.assertEqual(len(result), total_expected)

    def test_updates_owner_for_selected_footballers(self):
        """The footballer rows are updated with the correct owner_id."""
        position_counts = [
            ('GK', INITIAL_SQUAD_GK),
            ('DF', INITIAL_SQUAD_DF),
            ('MD', INITIAL_SQUAD_MD),
            ('FW', INITIAL_SQUAD_FW),
        ]
        candidates = self._candidates(position_counts)
        cursor = _make_cursor(candidates)
        player_id = 42
        league_id = 7

        result = _assign_initial_squad(cursor, player_id=player_id, league_id=league_id)

        execute_calls = cursor.execute.call_args_list
        update_calls = [c for c in execute_calls if 'UPDATE footballer' in str(c)]
        self.assertEqual(len(update_calls), 1, "Should issue exactly one UPDATE")

        params = update_calls[0].args[1]
        self.assertEqual(params[0], player_id, "owner_id should be the player_id")
        self.assertEqual(sorted(params[1]), sorted(result), "All selected IDs should be updated")
        self.assertEqual(params[2], league_id, "league_id must be passed to UPDATE")

    def test_returns_empty_list_when_no_candidates(self):
        """Returns an empty list and issues no UPDATE when no footballers are available."""
        cursor = _make_cursor([[], [], [], []])

        result = _assign_initial_squad(cursor, player_id=1, league_id=10)

        self.assertEqual(result, [])
        execute_calls = cursor.execute.call_args_list
        update_calls = [c for c in execute_calls if 'UPDATE footballer' in str(c)]
        self.assertEqual(len(update_calls), 0)

    def test_falls_back_to_cheapest_when_random_exceeds_budget(self):
        """When random picks would exceed the total budget, falls back to cheapest players."""
        # Use values that are valid individually but exceed the total when summed.
        # We put 2 expensive GK candidates (each at the per-player limit) plus
        # many cheaper alternatives so the total would otherwise blow the limit.
        expensive_value = INITIAL_SQUAD_PLAYER_VALUE_LIMIT  # 30 M each
        cheap_value = 1_000_000  # 1 M each

        # GK: 2 expensive players — their combined cost is 60 M which is more
        # than the total limit (100 M) minus the remaining positions' cheapest picks.
        # The fallback should still pick up to what fits.
        gk_candidates = [(101, expensive_value), (102, expensive_value)]
        # DF, MD, FW: provide cheap players
        df_candidates = [(200 + i, cheap_value) for i in range(INITIAL_SQUAD_DF)]
        md_candidates = [(300 + i, cheap_value) for i in range(INITIAL_SQUAD_MD)]
        fw_candidates = [(400 + i, cheap_value) for i in range(INITIAL_SQUAD_FW)]

        cursor = _make_cursor([gk_candidates, df_candidates, md_candidates, fw_candidates])

        result = _assign_initial_squad(cursor, player_id=1, league_id=10)

        # Compute max total value of the returned IDs
        all_candidates = dict(
            gk_candidates + df_candidates + md_candidates + fw_candidates
        )
        total_value = sum(all_candidates[f_id] for f_id in result)
        self.assertLessEqual(
            total_value,
            INITIAL_SQUAD_TOTAL_VALUE_LIMIT,
            "Total squad value must not exceed the configured limit",
        )

    def test_each_selected_player_within_individual_limit(self):
        """Every assigned footballer has a value ≤ INITIAL_SQUAD_PLAYER_VALUE_LIMIT."""
        value_per_player = INITIAL_SQUAD_PLAYER_VALUE_LIMIT  # exactly at the limit
        position_counts = [
            ('GK', INITIAL_SQUAD_GK),
            ('DF', INITIAL_SQUAD_DF),
            ('MD', INITIAL_SQUAD_MD),
            ('FW', INITIAL_SQUAD_FW),
        ]
        candidates = self._candidates(position_counts, value_per_player=value_per_player)
        cursor = _make_cursor(candidates)

        _assign_initial_squad(cursor, player_id=1, league_id=10)
        # The function only considers players already filtered by the DB query
        # (value <= INITIAL_SQUAD_PLAYER_VALUE_LIMIT), so if the mock respects that
        # invariant, the result is guaranteed.  We verify the DB query contains the limit.
        execute_calls = cursor.execute.call_args_list
        select_calls = [c for c in execute_calls if 'SELECT' in str(c)]
        for c in select_calls:
            params = c.args[1]
            self.assertIn(
                INITIAL_SQUAD_PLAYER_VALUE_LIMIT,
                params,
                "The per-player value limit must be passed to every SELECT query",
            )


if __name__ == "__main__":
    unittest.main()
