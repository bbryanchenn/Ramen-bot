TIER_BASE = {
    "IRON": 100,
    "BRONZE": 200,
    "SILVER": 300,
    "GOLD": 400,
    "PLATINUM": 500,
    "EMERALD": 600,
    "DIAMOND": 700,
    "MASTER": 800,
    "GRANDMASTER": 900,
    "CHALLENGER": 1000,
}

RANK_OFFSET = {
    "IV": 0,
    "III": 25,
    "II": 50,
    "I": 75,
}


def entry_to_mmr(entry: dict | None, default: int = 500) -> int:
    if not entry:
        return default

    tier = str(entry.get("tier", "")).upper()
    rank = str(entry.get("rank", "")).upper()
    lp = int(entry.get("leaguePoints", 0))

    if tier not in TIER_BASE:
        return default

    return TIER_BASE[tier] + RANK_OFFSET.get(rank, 0) + max(0, min(lp, 100))


def format_rank(entry: dict | None) -> str:
    if not entry:
        return "UNRANKED"
    tier = entry.get("tier", "UNRANKED")
    rank = entry.get("rank", "")
    lp = entry.get("leaguePoints", 0)
    wins = entry.get("wins", 0)
    losses = entry.get("losses", 0)
    return f"{tier} {rank} {lp} LP ({wins}W-{losses}L)"