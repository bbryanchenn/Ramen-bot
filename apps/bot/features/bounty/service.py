import json
from pathlib import Path

DATA_PATH = Path("data/bounties.json")


def _default_state() -> dict:
    return {"active": {}}


def load_bounties() -> dict:
    if not DATA_PATH.exists():
        return _default_state()
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return _default_state()

    if not isinstance(data, dict):
        return _default_state()

    data.setdefault("active", {})
    return data


def save_bounties(state: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def set_bounty(target_id: int, setter_id: int, amount: int) -> None:
    state = load_bounties()
    state["active"][str(target_id)] = {"setter_id": setter_id, "amount": amount}
    save_bounties(state)


def get_bounty(target_id: int) -> dict | None:
    state = load_bounties()
    return state["active"].get(str(target_id))


def clear_bounty(target_id: int) -> None:
    state = load_bounties()
    state["active"].pop(str(target_id), None)
    save_bounties(state)


def all_bounties() -> dict:
    return load_bounties()["active"]