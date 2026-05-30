from __future__ import annotations

from collections.abc import Iterable

from apps.bot.features.history.service import (
    latest_match_id_missing_recap,
    update_match,
)
from apps.bot.utils.storage import load_players
from core.riot.api import get_match_by_id, get_match_ids_by_puuid


RECENT_MATCH_LOOKBACK = 3
MIN_SHARED_PUUIDS = 4


def collect_team_puuids(
    blue_ids: Iterable[int],
    red_ids: Iterable[int],
) -> tuple[dict[str, int], dict[str, int]]:
    players = load_players()
    blue_map: dict[str, int] = {}
    red_map: dict[str, int] = {}

    for user_id in blue_ids:
        puuid = (players.get(int(user_id)) or {}).get("puuid")
        if puuid:
            blue_map[str(puuid)] = int(user_id)

    for user_id in red_ids:
        puuid = (players.get(int(user_id)) or {}).get("puuid")
        if puuid:
            red_map[str(puuid)] = int(user_id)

    return blue_map, red_map


def is_custom(match: dict) -> bool:
    info = match.get("info", {}) or {}
    if info.get("gameType") == "CUSTOM_GAME":
        return True
    return int(info.get("queueId", -1)) == 0


async def find_inhouse_match(
    candidate_puuids: list[str],
    inhouse_puuids: set[str],
) -> tuple[dict | None, str | None]:
    """Walk candidate puuids' recent match IDs; return the first custom match where ≥MIN_SHARED_PUUIDS inhouse puuids participated."""
    visited: set[str] = set()
    last_error: str | None = None

    for puuid in candidate_puuids:
        ids, error = await get_match_ids_by_puuid(puuid, count=RECENT_MATCH_LOOKBACK)
        if error:
            last_error = error
            continue

        for match_id in ids or []:
            if match_id in visited:
                continue
            visited.add(match_id)

            match, fetch_error = await get_match_by_id(match_id)
            if fetch_error or not match:
                last_error = fetch_error or "match fetch returned nothing"
                continue
            if not is_custom(match):
                continue

            participants = (match.get("info", {}) or {}).get("participants", []) or []
            participant_puuids = {str(p.get("puuid", "")) for p in participants}
            shared = participant_puuids & inhouse_puuids
            if len(shared) >= MIN_SHARED_PUUIDS:
                return match, None

    return None, last_error or "no shared custom match yet"


def _kill_participation(participant: dict, team_kills: int) -> float:
    if team_kills <= 0:
        return 0.0
    return (int(participant.get("kills", 0)) + int(participant.get("assists", 0))) / team_kills


def _damage_share(participant: dict, team_damage: int) -> float:
    if team_damage <= 0:
        return 0.0
    return int(participant.get("totalDamageDealtToChampions", 0)) / team_damage


def score_participant(participant: dict, team_kills: int, team_damage: int) -> float:
    kills = int(participant.get("kills", 0))
    deaths = int(participant.get("deaths", 0))
    assists = int(participant.get("assists", 0))

    kda = (kills + assists) / max(deaths, 1)
    kp = _kill_participation(participant, team_kills)
    ds = _damage_share(participant, team_damage)

    return round(kda * 1.5 + ds * 15.0 + kp * 5.0, 3)


def _majority_team_id(participants: list[dict], puuids: Iterable[str]) -> int | None:
    puuid_set = {str(p) for p in puuids}
    counts: dict[int, int] = {}
    for p in participants:
        if str(p.get("puuid", "")) in puuid_set:
            tid = int(p.get("teamId", 0))
            counts[tid] = counts.get(tid, 0) + 1
    if not counts:
        return None
    return max(counts.items(), key=lambda kv: kv[1])[0]


def summarize_match(
    match: dict,
    blue_puuids: dict[str, int],
    red_puuids: dict[str, int],
    declared_winner: str | None = None,
) -> dict:
    info = match.get("info", {}) or {}
    metadata = match.get("metadata", {}) or {}
    participants = info.get("participants", []) or []
    teams = info.get("teams", []) or []

    blue_team_id = _majority_team_id(participants, blue_puuids.keys())
    red_team_id = _majority_team_id(participants, red_puuids.keys())
    if blue_team_id is None and red_team_id is None:
        blue_team_id, red_team_id = 100, 200
    elif blue_team_id is None:
        blue_team_id = 200 if red_team_id == 100 else 100
    elif red_team_id is None:
        red_team_id = 200 if blue_team_id == 100 else 100

    team_kills = {blue_team_id: 0, red_team_id: 0}
    team_damage = {blue_team_id: 0, red_team_id: 0}
    for p in participants:
        tid = int(p.get("teamId", 0))
        if tid not in team_kills:
            continue
        team_kills[tid] += int(p.get("kills", 0))
        team_damage[tid] += int(p.get("totalDamageDealtToChampions", 0))

    rows: list[dict] = []
    for p in participants:
        puuid = str(p.get("puuid", ""))
        tid = int(p.get("teamId", 0))
        if tid == blue_team_id:
            side = "blue"
            user_id = blue_puuids.get(puuid)
        elif tid == red_team_id:
            side = "red"
            user_id = red_puuids.get(puuid)
        else:
            continue

        rows.append({
            "user_id": user_id,
            "puuid": puuid,
            "side": side,
            "champion": p.get("championName"),
            "champion_id": int(p.get("championId", 0)),
            "kills": int(p.get("kills", 0)),
            "deaths": int(p.get("deaths", 0)),
            "assists": int(p.get("assists", 0)),
            "gold": int(p.get("goldEarned", 0)),
            "damage": int(p.get("totalDamageDealtToChampions", 0)),
            "team_position": p.get("teamPosition") or p.get("individualPosition") or "",
            "win": bool(p.get("win", False)),
            "score": score_participant(p, team_kills.get(tid, 0), team_damage.get(tid, 0)),
        })

    riot_winner_team_id = next(
        (int(t.get("teamId")) for t in teams if t.get("win")),
        None,
    )
    if riot_winner_team_id == blue_team_id:
        winner = "blue"
    elif riot_winner_team_id == red_team_id:
        winner = "red"
    elif declared_winner:
        winner = declared_winner.lower()
    else:
        winner = "blue"

    winning_rows = [r for r in rows if r["side"] == winner]
    losing_rows = [r for r in rows if r["side"] != winner]

    mvp = max(winning_rows, key=lambda r: r["score"], default=None)
    diff = min(losing_rows, key=lambda r: r["score"], default=None)

    return {
        "match_id": metadata.get("matchId") or info.get("gameId"),
        "duration_s": int(info.get("gameDuration", 0)),
        "queue_id": int(info.get("queueId", -1)),
        "game_mode": info.get("gameMode"),
        "game_type": info.get("gameType"),
        "winner": winner,
        "blue_team_id": blue_team_id,
        "red_team_id": red_team_id,
        "participants": rows,
        "mvp_user_id": mvp.get("user_id") if mvp else None,
        "mvp_puuid": mvp.get("puuid") if mvp else None,
        "diff_user_id": diff.get("user_id") if diff else None,
        "diff_puuid": diff.get("puuid") if diff else None,
    }


def attach_recap_to_history(summary: dict) -> int | None:
    """Patch the most recent history row that's missing recap data. Returns the patched row id or None."""
    target_id = latest_match_id_missing_recap()
    if target_id is None:
        return None

    patch = {
        "mvp": summary.get("mvp_user_id"),
        "diff": summary.get("diff_user_id"),
        "riot_match_id": summary.get("match_id"),
        "riot_summary": {
            "duration_s": summary.get("duration_s"),
            "winner": summary.get("winner"),
            "participants": [
                {
                    "user_id": r["user_id"],
                    "side": r["side"],
                    "champion": r["champion"],
                    "kills": r["kills"],
                    "deaths": r["deaths"],
                    "assists": r["assists"],
                    "gold": r["gold"],
                    "damage": r["damage"],
                    "score": r["score"],
                    "team_position": r["team_position"],
                    "win": r["win"],
                }
                for r in summary.get("participants", [])
            ],
        },
    }

    return target_id if update_match(target_id, patch) else None
