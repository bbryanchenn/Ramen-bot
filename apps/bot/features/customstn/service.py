from __future__ import annotations

from datetime import datetime


YES_THRESHOLD = 1


class CustomSTNState(dict):
    channel_id: int
    created_by: int
    event_id: int | None
    message_id: int | None
    resolving: bool
    start_time: datetime
    yes_voters: set[int]


ACTIVE_CUSTOM_STNS: dict[int, CustomSTNState] = {}


def start_custom_stn(guild_id: int, channel_id: int, start_time: datetime, created_by: int) -> None:
    ACTIVE_CUSTOM_STNS[guild_id] = CustomSTNState(
        channel_id=int(channel_id),
        created_by=int(created_by),
        event_id=None,
        message_id=None,
        resolving=False,
        start_time=start_time,
        yes_voters=set(),
    )


def get_custom_stn(guild_id: int) -> CustomSTNState | None:
    return ACTIVE_CUSTOM_STNS.get(guild_id)


def has_active_custom_stn(guild_id: int) -> bool:
    state = ACTIVE_CUSTOM_STNS.get(guild_id)
    return bool(state and not state.get("resolving") and state.get("event_id") is None)


def bind_message(guild_id: int, message_id: int) -> None:
    state = ACTIVE_CUSTOM_STNS.get(guild_id)
    if state is None:
        return
    state["message_id"] = int(message_id)


def cast_yes_vote(guild_id: int, message_id: int, user_id: int) -> tuple[bool, str, int]:
    state = ACTIVE_CUSTOM_STNS.get(guild_id)
    if not state:
        return False, "No active custom vote is running.", 0

    if state.get("message_id") and int(state["message_id"]) != int(message_id):
        return False, "This vote message is no longer active.", len(state["yes_voters"])

    if state.get("event_id") is not None:
        return False, "The scheduled event has already been created.", len(state["yes_voters"])

    if state.get("resolving"):
        return False, "The scheduled event is being created right now.", len(state["yes_voters"])

    uid = int(user_id)
    if uid in state["yes_voters"]:
        return False, "You already voted yes.", len(state["yes_voters"])

    state["yes_voters"].add(uid)
    return True, "Vote counted.", len(state["yes_voters"])


def reserve_event_creation(guild_id: int) -> bool:
    state = ACTIVE_CUSTOM_STNS.get(guild_id)
    if not state:
        return False

    if state.get("event_id") is not None or state.get("resolving"):
        return False

    state["resolving"] = True
    return True


def finish_event_creation(guild_id: int, event_id: int) -> None:
    state = ACTIVE_CUSTOM_STNS.get(guild_id)
    if not state:
        return

    state["event_id"] = int(event_id)
    state["resolving"] = False


def abort_event_creation(guild_id: int) -> None:
    state = ACTIVE_CUSTOM_STNS.get(guild_id)
    if not state:
        return

    state["resolving"] = False


def clear_custom_stn(guild_id: int) -> None:
    ACTIVE_CUSTOM_STNS.pop(guild_id, None)
