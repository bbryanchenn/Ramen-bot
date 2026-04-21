from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.bot.utils.team_builder import assign_team, build_two_teams, can_fill_all_lanes  # noqa: E402
from core.scoring.player_score import LANES  # noqa: E402
from core.scoring.team_score import matchup_summary, score_team_assignment  # noqa: E402
from scripts.seed_db import generate_sample_players  # noqa: E402


class TeamBuilderSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.players = generate_sample_players(12, seed=17)

    def test_can_fill_all_lanes_for_balanced_roster(self) -> None:
        roster = self.players[:5]
        self.assertTrue(can_fill_all_lanes(roster))

    def test_assign_team_returns_full_lane_map(self) -> None:
        roster = self.players[:5]
        team = assign_team(roster)
        self.assertIsNotNone(team)
        self.assertEqual(set(team.keys()), set(LANES))
        self.assertLess(score_team_assignment(team), 10_000)

    def test_build_two_teams_returns_unique_players(self) -> None:
        random.seed(17)
        result = build_two_teams(self.players, tries=2500)
        self.assertIsNotNone(result)

        team1, team2 = result
        used_names = [player["name"] for player in team1.values()] + [player["name"] for player in team2.values()]
        self.assertEqual(len(used_names), 10)
        self.assertEqual(len(set(used_names)), 10)

        summary = matchup_summary(team1, team2)
        self.assertLessEqual(summary["total_mmr_diff"], 250)
        self.assertLess(summary["score"], 2_500)

    def test_build_two_teams_requires_ten_players(self) -> None:
        self.assertIsNone(build_two_teams(self.players[:9]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
