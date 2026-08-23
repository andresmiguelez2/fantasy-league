import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.app.api.routers.footballer import get_all_footballers


class FootballerRouterTests(unittest.TestCase):
    @patch("backend.app.api.routers.footballer.pg_connect")
    def test_get_all_footballers_applies_filters_and_returns_filter_options(
        self, mock_pg_connect
    ):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_cursor.fetchall.side_effect = [
            [
                (
                    1,
                    "Player One",
                    "Team A",
                    1000000,
                    "Owner",
                    5.5,
                    100,
                    "fw",
                    "available",
                )
            ],
            [("Team A", "fw", "available"), ("Team B", "df", "injured")],
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pg_connect.return_value = mock_conn

        response = get_all_footballers(
            league_id=7,
            page=2,
            limit=10,
            search="pla",
            teams="Team A,Team B",
            positions="fw",
            availabilities="available",
        )

        self.assertEqual(response["status"], "success")
        self.assertEqual(response["footballers"][0][2], "Team A")
        self.assertEqual(
            response["meta"]["filter_options"],
            {
                "teams": ["Team A", "Team B"],
                "positions": ["df", "fw"],
                "availabilities": ["available", "injured"],
            },
        )
        self.assertIn("team", response["columns"])

        count_query_args = mock_cursor.execute.call_args_list[0].args
        self.assertIn("fd.team = ANY(%s)", count_query_args[0])
        self.assertIn("fd.position = ANY(%s::position_type[])", count_query_args[0])
        self.assertIn(
            "fd.availability = ANY(%s::availability_type[])", count_query_args[0]
        )
        self.assertEqual(
            count_query_args[1],
            [7, "%pla%", ["Team A", "Team B"], ["fw"], ["available"]],
        )

        paged_query_args = mock_cursor.execute.call_args_list[1].args
        self.assertIn("fd.position = ANY(%s::position_type[])", paged_query_args[0])
        self.assertIn(
            "fd.availability = ANY(%s::availability_type[])", paged_query_args[0]
        )
        self.assertEqual(
            paged_query_args[1],
            [7, "%pla%", ["Team A", "Team B"], ["fw"], ["available"], 10, 10],
        )


if __name__ == "__main__":
    unittest.main()
