import json
import random
from pathlib import Path

DATA_PATH = Path("data/events.json")

EVENT_TYPES = {
    "SALT_SURGE": {"label": "🧂 Salt Surge"},
    "DOUBLE_DOWN": {"label": "💰 Double Down"},
    "UNDERDOG": {"label": "🎯 Underdog Blessing"},
    "MVP_BONUS": {"label": "🏆 MVP Bonus"},
}


def _default_state() -> dict:
    return {"active": None}


def load_events() -> dict:
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


def save_events(state: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def set_event(event_type: str) -> None:
    state = load_events()
    state["active"] = {"type": event_type}
    save_events(state)


def get_event() -> dict | None:
    return load_events().get("active")


def clear_event() -> None:
    state = load_events()
    state["active"] = None
    save_events(state)


def random_event_type() -> str:
    return random.choice(list(EVENT_TYPES.keys()))