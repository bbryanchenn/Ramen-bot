from core.builder.roles import LANES, autofill_count


def team_total_mmr(team: dict[str, dict]) -> int:
    return sum(player["mmr"] for player in team.values())


def mmr_spread(teams: list[dict[str, dict]]) -> int:
    totals = [team_total_mmr(team) for team in teams]
    return max(totals) - min(totals)


def average_team_mmr(teams: list[dict[str, dict]]) -> float:
    totals = [team_total_mmr(team) for team in teams]
    return sum(totals) / len(totals)


def total_autofills(teams: list[dict[str, dict]]) -> int:
    return sum(autofill_count(team) for team in teams)


def score_solution(teams: list[dict[str, dict]], bench_count: int = 0) -> int:
    spread = mmr_spread(teams)
    autofills = total_autofills(teams)
    return autofills * 1000 + spread * 2 + bench_count * 25


def team_summary(team: dict[str, dict]) -> dict:
    return {
        "total_mmr": team_total_mmr(team),
        "lanes": {lane: team[lane]["name"] for lane in LANES},
    }