import json
from pathlib import Path

from apps.bot.features.diffs.service import add_diff, add_mvp

DATA_PATH = Path("data/votes.json")


def _default_state() -> dict:
    return {
        "active": None
    }


def load_votes() -> dict:
    if not DATA_PATH.exists():
        return _default_state()

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return _default_state()

    if not isinstance(data, dict):
        return _default_state()

    data.setdefault("active", None)
    return data


def save_votes(state: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def start_vote(candidates: list[int]) -> None:
    state = load_votes()
    state["active"] = {
        "candidates": [int(x) for x in candidates],
        "mvp_votes": {},
        "diff_votes": {},
        "is_open": True,
    }
    save_votes(state)


def has_active_vote() -> bool:
    state = load_votes()
    active = state.get("active")
    return bool(active and active.get("is_open"))


def get_active_vote() -> dict | None:
    state = load_votes()
    return state.get("active")


def cast_vote(voter_id: int, target_id: int, category: str) -> tuple[bool, str]:
    state = load_votes()
    active = state.get("active")

    if not active or not active.get("is_open"):
        return False, "No active vote."

    if category not in ("mvp", "diff"):
        return False, "Invalid vote category."

    if int(target_id) not in active["candidates"]:
        return False, "That player is not a valid candidate."

    if int(voter_id) == int(target_id):
        return False, "You cannot vote for yourself."

    bucket = "mvp_votes" if category == "mvp" else "diff_votes"
    active[bucket][str(voter_id)] = int(target_id)
    save_votes(state)
    return True, "Vote recorded."


def tally_votes() -> dict | None:
    state = load_votes()
    active = state.get("active")

    if not active:
        return None

    
    mvp_counts: dict[int, int] = {}
    diff_counts: dict[int, int] = {}

    for _, target_id in active["mvp_votes"].items():
        target_id = int(target_id)
        mvp_counts[target_id] = mvp_counts.get(target_id, 0) + 1

    for _, target_id in active["diff_votes"].items():
        target_id = int(target_id)
        diff_counts[target_id] = diff_counts.get(target_id, 0) + 1

    mvp_winner = max(mvp_counts.items(), key=lambda x: x[1])[0] if mvp_counts else None
    diff_winner = max(diff_counts.items(), key=lambda x: x[1])[0] if diff_counts else None

    if mvp_winner is not None:
        add_mvp(mvp_winner)

    if diff_winner is not None:
        ok, _ = add_diff(diff_winner)
        if not ok:
            diff_winner = None  # invalidate if same as last

    state["active"] = None
    save_votes(state)

    return {
        "mvp_counts": mvp_counts,
        "diff_counts": diff_counts,
        "mvp_winner": mvp_winner,
        "diff_winner": diff_winner,
    }