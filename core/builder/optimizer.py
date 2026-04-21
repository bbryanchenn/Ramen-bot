import random

from core.builder.balance import evaluate_partition


def _sample_players(players: list[dict], count: int) -> tuple[list[dict], list[dict]]:
    selected = random.sample(players, count)
    selected_ids = {player["id"] for player in selected}
    bench = [player for player in players if player["id"] not in selected_ids]
    return selected, bench


def build_two_teams(players: list[dict], tries: int = 3000):
    if len(players) < 10:
        return None

    best_result = None
    best_score = float("inf")

    for _ in range(tries):
        selected, bench = _sample_players(players, 10)
        random.shuffle(selected)

        groups = [
            selected[:5],
            selected[5:10],
        ]

        result = evaluate_partition(groups, bench_count=len(bench))
        if result is None:
            continue

        if result["score"] < best_score:
            best_score = result["score"]
            best_result = {
                "teams": result["teams"],
                "bench": bench,
                "score": result["score"],
                "mode": 2,
            }

    return best_result


def build_three_teams(players: list[dict], tries: int = 5000):
    if len(players) < 15:
        return None

    best_result = None
    best_score = float("inf")

    for _ in range(tries):
        selected, bench = _sample_players(players, 15)
        random.shuffle(selected)

        groups = [
            selected[:5],
            selected[5:10],
            selected[10:15],
        ]

        result = evaluate_partition(groups, bench_count=len(bench))
        if result is None:
            continue

        if result["score"] < best_score:
            best_score = result["score"]
            best_result = {
                "teams": result["teams"],
                "bench": bench,
                "score": result["score"],
                "mode": 3,
            }

    return best_result


def build_best_lobby(players: list[dict], team_count: int, tries: int = 4000):
    if team_count == 2:
        return build_two_teams(players, tries=tries)
    if team_count == 3:
        return build_three_teams(players, tries=tries)
    return None