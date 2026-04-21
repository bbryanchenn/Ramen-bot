import json
from pathlib import Path

DATA_PATH = Path("data/players.json")


def load_players() -> dict:
    if not DATA_PATH.exists():
        return {}

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    players: dict[int, dict] = {}
    for key, value in data.items():
        try:
            user_id = int(key)
        except (TypeError, ValueError):
            continue

        if not isinstance(value, dict):
            continue

        player = value.copy()
        player.setdefault("manual_rank", False)
        player.setdefault("in_lobby", False)
        players[user_id] = player

    return players


def save_players(players: dict):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump({str(int(k)): v for k, v in players.items()}, f, indent=2)