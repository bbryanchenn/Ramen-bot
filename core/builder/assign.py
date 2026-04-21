import itertools

from core.builder.roles import LANES, can_play


def assign_team(players: list[dict]) -> dict[str, dict] | None:
    if len(players) != 5:
        return None

    for perm in itertools.permutations(players, 5):
        team = dict(zip(LANES, perm))
        if all(can_play(team[lane], lane) for lane in LANES):
            return team

    return None