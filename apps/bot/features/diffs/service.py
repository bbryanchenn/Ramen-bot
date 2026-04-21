import json
import random
from pathlib import Path

from apps.bot.features.diffs.messages import BLAME_MESSAGES

DATA_PATH = Path("data/diffs.json")


def _default_state() -> dict:
    return {
        "players": {}
    }


def load_diffs() -> dict:
    if not DATA_PATH.exists():
        return _default_state()

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return _default_state()

    if not isinstance(data, dict):
        return _default_state()

    data.setdefault("players", {})
    data.setdefault("last_diff", None)
    return data

def _default_state() -> dict:
    return {
        "players": {},
        "last_diff": None
    }



def save_diffs(state: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def ensure_player(state: dict, user_id: int) -> None:
    key = str(user_id)
    if key not in state["players"]:
        state["players"][key] = {
            "diffs": 0,
            "mvps": 0,
        }


def add_diff(user_id: int) -> tuple[bool, int]:
    state = load_diffs()

    last = state.get("last_diff")
    if last is not None and int(last) == int(user_id):
        return False, state["players"].get(str(user_id), {}).get("diffs", 0)

    ensure_player(state, user_id)

    key = str(user_id)
    state["players"][key]["diffs"] += 1
    total = state["players"][key]["diffs"]

    state["last_diff"] = int(user_id)

    save_diffs(state)
    return True, total


def add_mvp(user_id: int) -> int:
    state = load_diffs()
    ensure_player(state, user_id)
    key = str(user_id)
    state["players"][key]["mvps"] += 1
    total = state["players"][key]["mvps"]
    save_diffs(state)
    return total


def get_diff_count(user_id: int) -> int:
    state = load_diffs()
    ensure_player(state, user_id)
    return int(state["players"][str(user_id)]["diffs"])


def get_mvp_count(user_id: int) -> int:
    state = load_diffs()
    ensure_player(state, user_id)
    return int(state["players"][str(user_id)]["mvps"])


def top_diffs(limit: int = 10) -> list[tuple[int, int]]:
    state = load_diffs()
    rows = []
    for user_id, payload in state["players"].items():
        rows.append((int(user_id), int(payload.get("diffs", 0))))
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows[:limit]


def top_mvps(limit: int = 10) -> list[tuple[int, int]]:
    state = load_diffs()
    rows = []
    for user_id, payload in state["players"].items():
        rows.append((int(user_id), int(payload.get("mvps", 0))))
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows[:limit]


def random_blame_message() -> str:
    return random.choice(BLAME_MESSAGES)