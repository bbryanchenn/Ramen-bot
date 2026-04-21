from __future__ import annotations


ACTIVE_READY_CHECKS: dict[int, dict] = {}


def start_ready_check(guild_id: int, player_ids: list[int]) -> None:
    ACTIVE_READY_CHECKS[guild_id] = {
        "players": [int(x) for x in player_ids],
        "ready": [],
        "is_open": True,
        "message_id": None,
        "channel_id": None,
    }


def get_ready_check(guild_id: int) -> dict | None:
    return ACTIVE_READY_CHECKS.get(guild_id)


def has_ready_check(guild_id: int) -> bool:
    state = ACTIVE_READY_CHECKS.get(guild_id)
    return bool(state and state.get("is_open"))


def mark_ready(guild_id: int, user_id: int) -> tuple[bool, str]:
    state = ACTIVE_READY_CHECKS.get(guild_id)
    if not state or not state.get("is_open"):
        return False, "No active ready check."

    uid = int(user_id)
    if uid not in state["players"]:
        return False, "You are not part of this ready check."

    if uid in state["ready"]:
        return False, "You are already marked ready."

    state["ready"].append(uid)
    return True, "Ready confirmed."


def mark_unready(guild_id: int, user_id: int) -> tuple[bool, str]:
    state = ACTIVE_READY_CHECKS.get(guild_id)
    if not state or not state.get("is_open"):
        return False, "No active ready check."

    uid = int(user_id)
    if uid not in state["players"]:
        return False, "You are not part of this ready check."

    if uid not in state["ready"]:
        return False, "You are not marked ready."

    state["ready"].remove(uid)
    return True, "Marked unready."


def ready_count(guild_id: int) -> int:
    state = ACTIVE_READY_CHECKS.get(guild_id)
    if not state:
        return 0
    return len(state["ready"])


def total_count(guild_id: int) -> int:
    state = ACTIVE_READY_CHECKS.get(guild_id)
    if not state:
        return 0
    return len(state["players"])


def all_ready(guild_id: int) -> bool:
    state = ACTIVE_READY_CHECKS.get(guild_id)
    if not state:
        return False
    return len(state["ready"]) == len(state["players"])


def set_message_refs(guild_id: int, channel_id: int, message_id: int) -> None:
    state = ACTIVE_READY_CHECKS.get(guild_id)
    if not state:
        return
    state["channel_id"] = int(channel_id)
    state["message_id"] = int(message_id)


def get_missing_players(guild_id: int) -> list[int]:
    state = ACTIVE_READY_CHECKS.get(guild_id)
    if not state:
        return []
    ready = set(state["ready"])
    return [uid for uid in state["players"] if uid not in ready]


def end_ready_check(guild_id: int) -> dict | None:
    state = ACTIVE_READY_CHECKS.get(guild_id)
    if not state:
        return None

    state["is_open"] = False
    return state


def clear_ready_check(guild_id: int) -> None:
    ACTIVE_READY_CHECKS.pop(guild_id, None)