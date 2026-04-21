ROLE_NAMES = {"TOP", "JUNGLE", "MID", "ADC", "SUPPORT", "FILL"}


def extract_player_roles(member) -> list[str]:
    roles = []

    for role in member.roles:
        name = role.name.strip().upper()
        if name in ROLE_NAMES:
            roles.append(name)

    if "FILL" in roles and len(roles) == 1:
        return ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]

    out = [r for r in roles if r != "FILL"]

    if not out and "FILL" in roles:
        return ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]

    return out