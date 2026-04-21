import json
from pathlib import Path

from apps.bot.features.titles.catalog import TITLE_CATALOG

DATA_PATH = Path("data/titles.json")


def _default_state() -> dict:
    return {
        "players": {}
    }


def load_titles() -> dict:
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
    return data


def save_titles(state: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def ensure_user(state: dict, user_id: int) -> None:
    key = str(user_id)
    if key not in state["players"]:
        state["players"][key] = {
            "owned": [],
            "equipped": None,
        }


def get_user_titles(user_id: int) -> dict:
    state = load_titles()
    ensure_user(state, user_id)
    return state["players"][str(user_id)]


def owns_title(user_id: int, title_key: str) -> bool:
    state = load_titles()
    ensure_user(state, user_id)
    return title_key in state["players"][str(user_id)]["owned"]


def equipped_title(user_id: int) -> str | None:
    state = load_titles()
    ensure_user(state, user_id)
    return state["players"][str(user_id)]["equipped"]


def buy_title(user_id: int, title_key: str) -> tuple[bool, str]:
    if title_key not in TITLE_CATALOG:
        return False, "Invalid title."

    state = load_titles()
    ensure_user(state, user_id)

    player = state["players"][str(user_id)]
    if title_key in player["owned"]:
        return False, "You already own that title."

    from apps.bot.features.betting.service import load_bets, save_bets, get_balance, add_balance

    bets_state = load_bets()
    balance = get_balance(bets_state, user_id)
    price = TITLE_CATALOG[title_key]["price"]

    if balance < price:
        return False, f"You need {price} coins."

    add_balance(bets_state, user_id, -price)
    save_bets(bets_state)

    player["owned"].append(title_key)
    if player["equipped"] is None:
        player["equipped"] = title_key

    save_titles(state)
    return True, f"Bought {TITLE_CATALOG[title_key]['name']} for {price} coins."


def equip_title(user_id: int, title_key: str) -> tuple[bool, str]:
    if title_key not in TITLE_CATALOG:
        return False, "Invalid title."

    state = load_titles()
    ensure_user(state, user_id)

    player = state["players"][str(user_id)]
    if title_key not in player["owned"]:
        return False, "You do not own that title."

    player["equipped"] = title_key
    save_titles(state)
    return True, f"Equipped {TITLE_CATALOG[title_key]['name']}."


def get_equipped_title_name(user_id: int) -> str | None:
    key = equipped_title(user_id)
    if not key:
        return None
    if key not in TITLE_CATALOG:
        return None
    return TITLE_CATALOG[key]["name"]