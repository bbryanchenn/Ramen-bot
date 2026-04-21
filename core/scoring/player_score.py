from __future__ import annotations

from typing import Any, Mapping

LANES = ("TOP", "JUNGLE", "MID", "ADC", "SUPPORT")
DEFAULT_MMR = 500
INVALID_ROLE_PENALTY = 10_000


def normalize_roles(player: Mapping[str, Any]) -> tuple[str, ...]:
    """Return a cleaned, de-duplicated lane list for a player."""
    raw_roles = player.get("role_preferences") or player.get("roles") or ()
    normalized: list[str] = []
    seen: set[str] = set()

    for role in raw_roles:
        role_name = str(role).strip().upper()
        if role_name in LANES and role_name not in seen:
            normalized.append(role_name)
            seen.add(role_name)

    return tuple(normalized)


def player_mmr(player: Mapping[str, Any], default: int = DEFAULT_MMR) -> int:
    raw_value = player.get("mmr", default)
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def can_play_lane(player: Mapping[str, Any], lane: str) -> bool:
    return lane.strip().upper() in normalize_roles(player)


def role_flexibility(player: Mapping[str, Any]) -> int:
    return max(0, len(normalize_roles(player)) - 1)


def preferred_role_index(player: Mapping[str, Any], lane: str) -> int | None:
    lane_name = lane.strip().upper()
    roles = normalize_roles(player)
    try:
        return roles.index(lane_name)
    except ValueError:
        return None


def lane_fit_penalty(player: Mapping[str, Any], lane: str) -> int:
    """Lower is better.

    If `role_preferences` is present, we honor that order. Otherwise we fall
    back to the order of `roles` as a weak tie-breaker between valid layouts.
    """
    role_index = preferred_role_index(player, lane)
    if role_index is None:
        return INVALID_ROLE_PENALTY

    return role_index * 12


def player_score(player: Mapping[str, Any], lane: str | None = None) -> dict[str, Any]:
    roles = normalize_roles(player)
    summary = {
        "name": player.get("name", "Unknown"),
        "mmr": player_mmr(player),
        "roles": list(roles),
        "flex_roles": role_flexibility(player),
    }

    if lane is not None:
        summary["lane"] = lane.strip().upper()
        summary["lane_penalty"] = lane_fit_penalty(player, lane)
        summary["can_play_lane"] = can_play_lane(player, lane)

    return summary
