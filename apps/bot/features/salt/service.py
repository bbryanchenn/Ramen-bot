import json
from pathlib import Path

DATA_PATH = Path("data/salt.json")

DEFAULT_STATE = {
    "salt": 0
}


def load_salt():
    if not DATA_PATH.exists():
        return DEFAULT_STATE.copy()

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return DEFAULT_STATE.copy()

    if not isinstance(data, dict):
        return DEFAULT_STATE.copy()

    data.setdefault("salt", 0)
    return data


def save_salt(state: dict):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def get_salt_value() -> int:
    state = load_salt()
    return int(state.get("salt", 0))


def set_salt_value(value: int):
    state = load_salt()
    state["salt"] = max(0, int(value))
    save_salt(state)


def add_salt(amount: int):
    state = load_salt()
    state["salt"] = max(0, int(state["salt"]) + int(amount))
    save_salt(state)
    return state["salt"]


def reset_salt():
    state = {"salt": 0}
    save_salt(state)


def get_multiplier() -> float:
    salt = get_salt_value()
    return min(2.0, 1.0 + salt * 0.1)