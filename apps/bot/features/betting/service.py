import json
from pathlib import Path

from apps.bot.features.betting.constants import STARTING_BALANCE

DATA_PATH = Path("data/bets.json")


def _default_state() -> dict:
    return {
        "balances": {},
        "stats": {},
        "current_bets": {
            "blue": {},
            "red": {},
        },
        "insurance": {},
        "current_match": {
            "blue_team": [],
            "red_team": [],
            "bets_locked": False,
        },
    }


def load_bets() -> dict:
    if not DATA_PATH.exists():
        return _default_state()

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return _default_state()

    state = _default_state()
    if isinstance(data, dict):
        state.update(data)

    state.setdefault("balances", {})
    state.setdefault("stats", {})
    state.setdefault("current_bets", {"blue": {}, "red": {}})
    state["current_bets"].setdefault("blue", {})
    state["current_bets"].setdefault("red", {})
    state.setdefault("insurance", {})
    state.setdefault("current_match", {"blue_team": [], "red_team": [], "bets_locked": False})
    state["current_match"].setdefault("blue_team", [])
    state["current_match"].setdefault("red_team", [])
    state["current_match"].setdefault("bets_locked", False)

    return state


def _get_current_match(state: dict) -> dict:
    match = state.setdefault("current_match", {"blue_team": [], "red_team": [], "bets_locked": False})
    match.setdefault("blue_team", [])
    match.setdefault("red_team", [])
    match.setdefault("bets_locked", False)
    return match


def save_bets(state: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def ensure_user(state: dict, user_id: int) -> None:
    key = str(user_id)

    if key not in state["balances"]:
        state["balances"][key] = STARTING_BALANCE

    if key not in state["stats"]:
        state["stats"][key] = {
            "profit": 0,
            "total_bet": 0,
            "bets_placed": 0,
            "wins": 0,
            "losses": 0,
            "biggest_win": 0,
            "biggest_loss": 0,
        }

    if key not in state["insurance"]:
        state["insurance"][key] = False


def get_balance(state: dict, user_id: int) -> int:
    ensure_user(state, user_id)
    return int(state["balances"][str(user_id)])


def set_balance(state: dict, user_id: int, amount: int) -> None:
    ensure_user(state, user_id)
    state["balances"][str(user_id)] = max(0, int(amount))


def add_balance(state: dict, user_id: int, amount: int) -> int:
    ensure_user(state, user_id)
    key = str(user_id)
    state["balances"][key] = max(0, int(state["balances"][key]) + int(amount))
    return int(state["balances"][key])


def add_profit(state: dict, user_id: int, amount: int) -> None:
    ensure_user(state, user_id)
    key = str(user_id)
    state["stats"][key]["profit"] += int(amount)


def add_bet_stats(state: dict, user_id: int, amount: int) -> None:
    ensure_user(state, user_id)
    key = str(user_id)
    state["stats"][key]["total_bet"] += int(amount)
    state["stats"][key]["bets_placed"] += 1


def record_win(state: dict, user_id: int, amount: int) -> None:
    ensure_user(state, user_id)
    key = str(user_id)
    state["stats"][key]["wins"] += 1
    state["stats"][key]["profit"] += int(amount)
    state["stats"][key]["biggest_win"] = max(int(state["stats"][key]["biggest_win"]), int(amount))


def record_loss(state: dict, user_id: int, amount: int) -> None:
    ensure_user(state, user_id)
    key = str(user_id)
    loss_amount = abs(int(amount))
    state["stats"][key]["losses"] += 1
    state["stats"][key]["profit"] -= loss_amount
    state["stats"][key]["biggest_loss"] = max(int(state["stats"][key]["biggest_loss"]), loss_amount)


def has_insurance(state: dict, user_id: int) -> bool:
    ensure_user(state, user_id)
    return bool(state["insurance"][str(user_id)])


def set_insurance(state: dict, user_id: int, enabled: bool) -> None:
    ensure_user(state, user_id)
    state["insurance"][str(user_id)] = bool(enabled)


def clear_current_bets(state: dict) -> None:
    state["current_bets"] = {"blue": {}, "red": {}}
    state["insurance"] = {}
    state["current_match"] = {
        "blue_team": [],
        "red_team": [],
        "bets_locked": False,
    }


def set_current_match(state: dict, blue_team_ids: list[int], red_team_ids: list[int]) -> None:
    state["current_match"] = {
        "blue_team": [int(x) for x in blue_team_ids],
        "red_team": [int(x) for x in red_team_ids],
        "bets_locked": False,
    }
    state["current_bets"] = {"blue": {}, "red": {}}
    state["insurance"] = {}


def lock_bets(state: dict) -> None:
    _get_current_match(state)["bets_locked"] = True


def bets_locked(state: dict) -> bool:
    return bool(_get_current_match(state).get("bets_locked", False))


def leave_sides(state: dict, user_id: int) -> dict:
    uid = int(user_id)
    match = _get_current_match(state)
    match["blue_team"] = [int(x) for x in match.get("blue_team", []) if int(x) != uid]
    match["red_team"] = [int(x) for x in match.get("red_team", []) if int(x) != uid]
    return match


def join_side(state: dict, user_id: int, side: str) -> dict:
    side = side.lower()
    if side not in ("blue", "red"):
        raise ValueError("side must be 'blue' or 'red'")

    uid = int(user_id)
    match = leave_sides(state, uid)

    team_key = "blue_team" if side == "blue" else "red_team"
    if uid not in match[team_key]:
        match[team_key].append(uid)

    return match


def is_player_in_current_match(state: dict, user_id: int) -> bool:
    uid = int(user_id)
    match = state.get("current_match", {})
    return uid in match.get("blue_team", []) or uid in match.get("red_team", [])


def place_bet(state: dict, user_id: int, team: str, amount: int) -> tuple[bool, str]:
    team = team.lower()
    if team not in ("blue", "red"):
        return False, "Team must be blue or red."

    ensure_user(state, user_id)

    if bets_locked(state):
        return False, "Bets are locked for the current match."

    if is_player_in_current_match(state, user_id):
        return False, "Players in the current match cannot bet."

    balance = get_balance(state, user_id)
    if amount <= 0:
        return False, "Bet amount must be positive."
    if amount > balance:
        return False, "You do not have enough coins."

    key = str(user_id)

    old_blue = int(state["current_bets"]["blue"].get(key, 0))
    old_red = int(state["current_bets"]["red"].get(key, 0))
    old_total = old_blue + old_red

    if old_total > 0:
        add_balance(state, user_id, old_total)

    state["current_bets"]["blue"].pop(key, None)
    state["current_bets"]["red"].pop(key, None)

    add_balance(state, user_id, -amount)
    state["current_bets"][team][key] = amount
    add_bet_stats(state, user_id, amount)

    return True, f"Bet placed: {amount} on {team.title()}."


def get_pool_totals(state: dict) -> tuple[int, int]:
    blue_total = sum(int(v) for v in state["current_bets"]["blue"].values())
    red_total = sum(int(v) for v in state["current_bets"]["red"].values())
    return blue_total, red_total