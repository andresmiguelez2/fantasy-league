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
    INITIAL_SQUAD_TOTAL_VALUE_TOLERANCE,
)

LOWER_BOUND = round(INITIAL_SQUAD_TOTAL_VALUE_LIMIT * (1 - INITIAL_SQUAD_TOTAL_VALUE_TOLERANCE))


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
        candidates = self._candidates(position_counts, value_per_player=5_500_000)
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
        candidates = self._candidates(position_counts, value_per_player=5_500_000)
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

    def test_squad_value_within_tolerance_of_limit(self):
        """Total squad value is within ±INITIAL_SQUAD_TOTAL_VALUE_TOLERANCE of the limit
        when sufficient high-value candidates are available."""
        # Each player at 5.5 M → 18 × 5.5 M = 99 M ∈ [90 M, 100 M]
        value_per_player = 5_500_000
        position_counts = [
            ('GK', INITIAL_SQUAD_GK),
            ('DF', INITIAL_SQUAD_DF),
            ('MD', INITIAL_SQUAD_MD),
            ('FW', INITIAL_SQUAD_FW),
        ]
        candidates = self._candidates(position_counts, value_per_player=value_per_player)
        cursor = _make_cursor(candidates)

        result = _assign_initial_squad(cursor, player_id=1, league_id=10)

        total_value = len(result) * value_per_player
        self.assertGreaterEqual(total_value, LOWER_BOUND,
                                "Total squad value must be at least 10% below the limit")
        self.assertLessEqual(total_value, INITIAL_SQUAD_TOTAL_VALUE_LIMIT,
                             "Total squad value must not exceed the limit")

    def test_upgrade_raises_value_towards_lower_bound(self):
        """When cheap players are initially selected, the upgrade step swaps them for
        more expensive alternatives so the total reaches the lower bound."""
        # GK: 2 cheap (1 M each) + 2 expensive upgrades (28 M each)
        # DF: 6 cheap (1 M each) + 6 expensive upgrades (10 M each)
        # MD/FW: exact-count cheap players only (no upgrades available)
        # Without upgrades: 18 × 1 M = 18 M  (well below 90 M)
        # After GK upgrades: 2×28 M + 16×1 M = 72 M  (still below 90 M)
        # After DF upgrades (partial): greedily adds expensive DF until ≥ 90 M
        cheap = 1_000_000
        gk_candidates = [(1, cheap), (2, cheap), (3, 28_000_000), (4, 28_000_000)]
        df_candidates = [(10 + i, cheap) for i in range(INITIAL_SQUAD_DF)] + \
                        [(20 + i, 10_000_000) for i in range(INITIAL_SQUAD_DF)]
        md_candidates = [(30 + i, cheap) for i in range(INITIAL_SQUAD_MD)]
        fw_candidates = [(40 + i, cheap) for i in range(INITIAL_SQUAD_FW)]

        all_cands = dict(gk_candidates + df_candidates + md_candidates + fw_candidates)

        cursor = _make_cursor([gk_candidates, df_candidates, md_candidates, fw_candidates])

        result = _assign_initial_squad(cursor, player_id=1, league_id=10)

        total_value = sum(all_cands[f_id] for f_id in result)
        self.assertLessEqual(total_value, INITIAL_SQUAD_TOTAL_VALUE_LIMIT,
                             "Total squad value must not exceed the upper limit")
        self.assertGreaterEqual(total_value, LOWER_BOUND,
                                "Upgrade step must raise total to at least the lower bound")

    def test_downgrade_when_random_exceeds_limit(self):
        """When the random draw exceeds the total limit, cheaper players are chosen instead."""
        # 18 players each at the per-player cap (30 M) → 540 M if all selected.
        # The downgrade step must ensure the total stays ≤ 100 M.
        value_per_player = INITIAL_SQUAD_PLAYER_VALUE_LIMIT  # 30 M
        position_counts = [
            ('GK', INITIAL_SQUAD_GK),
            ('DF', INITIAL_SQUAD_DF),
            ('MD', INITIAL_SQUAD_MD),
            ('FW', INITIAL_SQUAD_FW),
        ]
        # Provide exactly `count` candidates per position so there are no alternatives
        candidates = self._candidates(position_counts, value_per_player=value_per_player)
        cursor = _make_cursor(candidates)

        result = _assign_initial_squad(cursor, player_id=1, league_id=10)

        all_cands = {}
        start_id = 1
        for _, count in position_counts:
            for i in range(count):
                all_cands[start_id + i] = value_per_player
            start_id += count

        total_value = sum(all_cands[f_id] for f_id in result)
        self.assertLessEqual(total_value, INITIAL_SQUAD_TOTAL_VALUE_LIMIT,
                             "Total squad value must not exceed the configured limit")

    def test_each_selected_player_within_individual_limit(self):
        """Every assigned footballer has a value ≤ INITIAL_SQUAD_PLAYER_VALUE_LIMIT."""
        position_counts = [
            ('GK', INITIAL_SQUAD_GK),
            ('DF', INITIAL_SQUAD_DF),
            ('MD', INITIAL_SQUAD_MD),
            ('FW', INITIAL_SQUAD_FW),
        ]
        candidates = self._candidates(position_counts, value_per_player=5_500_000)
        cursor = _make_cursor(candidates)

        _assign_initial_squad(cursor, player_id=1, league_id=10)
        # Verify the DB query filters by the per-player value limit
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

