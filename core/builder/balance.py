from core.builder.assign import assign_team
from core.builder.roles import can_fill_all_lanes
from core.builder.scoring import score_solution


def evaluate_partition(groups: list[list[dict]], bench_count: int = 0):
    teams = []

    for group in groups:
        if not can_fill_all_lanes(group):
            return None

        team = assign_team(group)
        if team is None:
            return None

        teams.append(team)

    score = score_solution(teams, bench_count=bench_count)
    return {
        "teams": teams,
        "score": score,
        "bench_count": bench_count,
    }