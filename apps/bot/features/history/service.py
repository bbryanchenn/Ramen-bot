import json
from pathlib import Path

DATA_PATH = Path("data/history.json")


def _default_state() -> dict:
    return {"matches": [], "next_id": 1}


def load_history() -> dict:
    if not DATA_PATH.exists():
        return _default_state()
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return _default_state()

    if not isinstance(data, dict):
        return _default_state()

    data.setdefault("matches", [])
    data.setdefault("next_id", 1)
    return data


def save_history(state: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def add_match(match_data: dict) -> int:
    state = load_history()
    match_id = int(state["next_id"])
    payload = {"id": match_id, **match_data}
    state["matches"].append(payload)
    state["next_id"] = match_id + 1
    save_history(state)
    return match_id


def latest_matches(limit: int = 10) -> list[dict]:
    state = load_history()
    return list(reversed(state["matches"][-limit:]))


def user_matches(user_id: int, limit: int = 10) -> list[dict]:
    rows = []
    for match in latest_matches(100):
        blue = set(match.get("blue_team", []))
        red = set(match.get("red_team", []))
        if user_id in blue or user_id in red:
            rows.append(match)
        if len(rows) >= limit:
            break
    return rows