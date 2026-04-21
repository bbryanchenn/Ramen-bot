import itertools
import random

from core.scoring.player_score import LANES, can_play_lane
from core.scoring.team_score import score_matchup, score_team_assignment, team_total_mmr


def valid_for_lane(player: dict, lane: str) -> bool:
    return can_play_lane(player, lane)


def team_mmr(team: dict[str, dict]) -> int:
    return team_total_mmr(team)


def can_fill_all_lanes(players: list[dict]) -> bool:
    for lane in LANES:
        if not any(valid_for_lane(p, lane) for p in players):
            return False
    return True


def assign_team(players: list[dict]) -> dict[str, dict] | None:
    best_team = None
    best_score = float("inf")

    for perm in itertools.permutations(players, len(LANES)):
        team = dict(zip(LANES, perm))
        if all(valid_for_lane(team[lane], lane) for lane in LANES):
            score = score_team_assignment(team)
            if score < best_score:
                best_score = score
                best_team = team

    return best_team


def build_two_teams(players: list[dict], tries: int = 3000):
    required_players = len(LANES) * 2
    if len(players) < required_players:
        return None

    best = None
    best_score = float("inf")

    for _ in range(tries):
        sample = random.sample(players, required_players)
        random.shuffle(sample)

        left = sample[: len(LANES)]
        right = sample[len(LANES) :]

        if not can_fill_all_lanes(left) or not can_fill_all_lanes(right):
            continue

        team1 = assign_team(left)
        team2 = assign_team(right)

        if team1 is None or team2 is None:
            continue

        score = score_matchup(team1, team2)

        if score < best_score:
            best_score = score
            best = (team1, team2)

    return best
