LANES = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]


def normalize_roles(roles: list[str]) -> list[str]:
    out = []
    for role in roles:
        r = role.strip().upper()
        if r == "FILL":
            return LANES.copy()
        if r in LANES and r not in out:
            out.append(r)
    return out


def can_play(player: dict, lane: str) -> bool:
    return lane in player.get("roles", [])


def can_fill_all_lanes(players: list[dict]) -> bool:
    for lane in LANES:
        if not any(can_play(player, lane) for player in players):
            return False
    return True


def autofill_count(team: dict[str, dict]) -> int:
    count = 0
    for lane, player in team.items():
        if lane not in player.get("roles", []):
            count += 1
    return count