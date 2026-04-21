from __future__ import annotations

import argparse
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apps.bot.utils.team_builder import build_two_teams  # noqa: E402
from core.scoring.player_score import LANES  # noqa: E402
from core.scoring.team_score import matchup_summary  # noqa: E402
from scripts.seed_db import generate_sample_players, load_players_from_db  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Draft teams and simulate a simple inhouse tournament.")
    parser.add_argument("--rounds", type=int, default=5, help="How many rounds to simulate.")
    parser.add_argument("--best-of", type=int, default=3, help="Series length for each drafted matchup.")
    parser.add_argument("--tries", type=int, default=3000, help="How many team-builder attempts to use per round.")
    parser.add_argument("--player-count", type=int, default=10, help="How many players to load or generate.")
    parser.add_argument("--seed", type=int, default=21, help="Random seed for deterministic simulations.")
    parser.add_argument("--from-db", action="store_true", help="Load players from DATABASE_URL instead of generating them.")
    return parser


def load_players(player_count: int, *, seed: int, from_db: bool) -> list[dict]:
    if from_db:
        players = load_players_from_db(limit=player_count)
        if len(players) < 10:
            raise RuntimeError("The database must contain at least 10 players to run a simulation.")
        return players

    return generate_sample_players(max(10, player_count), seed=seed)


def win_probability(summary: dict[str, object]) -> float:
    mmr_delta = float(summary["team1_total_mmr"]) - float(summary["team2_total_mmr"])
    return 1.0 / (1.0 + math.exp(-mmr_delta / 200.0))


def simulate_series(team1: dict[str, dict], team2: dict[str, dict], *, best_of: int, rng: random.Random) -> tuple[int, int]:
    needed_wins = best_of // 2 + 1
    team1_wins = 0
    team2_wins = 0

    summary = matchup_summary(team1, team2)
    team1_odds = win_probability(summary)

    while team1_wins < needed_wins and team2_wins < needed_wins:
        if rng.random() < team1_odds:
            team1_wins += 1
        else:
            team2_wins += 1

    return team1_wins, team2_wins


def format_team(team: dict[str, dict]) -> str:
    lines = []
    for lane in LANES:
        player = team[lane]
        lines.append(f"  {lane:<7} {player['name']:<12} MMR {player['mmr']}")
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    rng = random.Random(args.seed)
    random.seed(args.seed)

    players = load_players(args.player_count, seed=args.seed, from_db=args.from_db)
    standings: dict[str, dict[str, int]] = defaultdict(lambda: {"games": 0, "wins": 0, "losses": 0, "series_wins": 0, "series_losses": 0})

    for round_number in range(1, args.rounds + 1):
        result = build_two_teams(players, tries=args.tries)
        if result is None:
            raise RuntimeError("Team builder could not create a valid 5v5 matchup from the supplied players.")

        team1, team2 = result
        summary = matchup_summary(team1, team2)
        team1_wins, team2_wins = simulate_series(team1, team2, best_of=args.best_of, rng=rng)

        winner = team1 if team1_wins > team2_wins else team2
        loser = team2 if winner is team1 else team1

        print(f"Round {round_number}")
        print(f"Team 1 total MMR: {summary['team1_total_mmr']}")
        print(format_team(team1))
        print(f"Team 2 total MMR: {summary['team2_total_mmr']}")
        print(format_team(team2))
        print(f"Matchup score: {summary['score']:.2f} | MMR diff: {summary['total_mmr_diff']}")
        print(f"Series result: Team 1 {team1_wins} - {team2_wins} Team 2")
        print("")

        for player in team1.values():
            standings[player["name"]]["games"] += team1_wins + team2_wins
            standings[player["name"]]["wins"] += team1_wins
            standings[player["name"]]["losses"] += team2_wins

        for player in team2.values():
            standings[player["name"]]["games"] += team1_wins + team2_wins
            standings[player["name"]]["wins"] += team2_wins
            standings[player["name"]]["losses"] += team1_wins

        for player in winner.values():
            standings[player["name"]]["series_wins"] += 1

        for player in loser.values():
            standings[player["name"]]["series_losses"] += 1

    print("Standings")
    for name, record in sorted(
        standings.items(),
        key=lambda item: (
            -item[1]["series_wins"],
            -item[1]["wins"],
            item[1]["losses"],
            item[0],
        ),
    ):
        print(
            f"{name:<12} "
            f"series {record['series_wins']}-{record['series_losses']} | "
            f"games {record['wins']}-{record['losses']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
