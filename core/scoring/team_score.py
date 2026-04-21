from __future__ import annotations

from typing import Any, Mapping

from core.scoring.player_score import INVALID_ROLE_PENALTY, LANES, lane_fit_penalty, player_mmr

Team = Mapping[str, Mapping[str, Any]]


def team_total_mmr(team: Team) -> int:
    return sum(player_mmr(player) for player in team.values())


def team_average_mmr(team: Team) -> float:
    if not team:
        return 0.0
    return team_total_mmr(team) / len(team)


def score_team_assignment(team: Team) -> int:
    penalty = 0

    for lane in LANES:
        player = team.get(lane)
        if player is None:
            penalty += INVALID_ROLE_PENALTY
            continue
        penalty += lane_fit_penalty(player, lane)

    return penalty


def lane_mmr_deltas(team1: Team, team2: Team) -> dict[str, int]:
    return {
        lane: abs(player_mmr(team1.get(lane, {})) - player_mmr(team2.get(lane, {})))
        for lane in LANES
    }


def matchup_summary(team1: Team, team2: Team) -> dict[str, Any]:
    total1 = team_total_mmr(team1)
    total2 = team_total_mmr(team2)
    lane_diffs = lane_mmr_deltas(team1, team2)
    total_diff = abs(total1 - total2)
    max_lane_diff = max(lane_diffs.values(), default=0)
    lane_gap_sum = sum(lane_diffs.values())
    assignment_penalty = score_team_assignment(team1) + score_team_assignment(team2)

    # Team total MMR matters most, then lane parity, then role-preference fit.
    score = (
        total_diff * 4.0
        + lane_gap_sum * 1.25
        + max_lane_diff * 2.0
        + assignment_penalty * 3.0
    )

    return {
        "team1_total_mmr": total1,
        "team2_total_mmr": total2,
        "team1_average_mmr": team_average_mmr(team1),
        "team2_average_mmr": team_average_mmr(team2),
        "total_mmr_diff": total_diff,
        "lane_diffs": lane_diffs,
        "max_lane_diff": max_lane_diff,
        "lane_gap_sum": lane_gap_sum,
        "assignment_penalty": assignment_penalty,
        "score": score,
    }


def score_matchup(team1: Team, team2: Team) -> float:
    return float(matchup_summary(team1, team2)["score"])
