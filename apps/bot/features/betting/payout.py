from apps.bot.features.betting.constants import INSURANCE_REFUND_RATIO, PLAYER_WIN_REWARD
from apps.bot.features.betting.service import (
    add_balance,
    get_pool_totals,
    has_insurance,
    record_loss,
    record_win,
    set_insurance,
)


def payout_multiplier_from_salt(salt: int) -> float:
    return min(2.0, 1.0 + max(0, salt) * 0.1)


def settle_match(state: dict, winning_team: str, salt: int) -> dict:
    winning_team = winning_team.lower()
    losing_team = "red" if winning_team == "blue" else "blue"

    blue_total, red_total = get_pool_totals(state)
    win_pool = blue_total if winning_team == "blue" else red_total
    lose_pool = red_total if winning_team == "blue" else blue_total
    total_pool = win_pool + lose_pool

    multiplier = payout_multiplier_from_salt(salt)
    results = {
        "multiplier": multiplier,
        "player_rewards": [],
        "bet_winners": [],
        "bet_losers": [],
        "blue_total": blue_total,
        "red_total": red_total,
    }

    win_team_ids = state["current_match"]["blue_team"] if winning_team == "blue" else state["current_match"]["red_team"]

    player_reward = int(round(PLAYER_WIN_REWARD * multiplier))
    for user_id in win_team_ids:
        add_balance(state, int(user_id), player_reward)
        results["player_rewards"].append({
            "user_id": int(user_id),
            "reward": player_reward,
        })

    winners = state["current_bets"][winning_team]
    losers = state["current_bets"][losing_team]

    if win_pool > 0:
        for user_id_str, bet_amount in winners.items():
            bet_amount = int(bet_amount)
            payout = int(round((bet_amount / win_pool) * total_pool * multiplier))
            add_balance(state, int(user_id_str), payout)
            record_win(state, int(user_id_str), payout - bet_amount)
            results["bet_winners"].append({
                "user_id": int(user_id_str),
                "bet": bet_amount,
                "payout": payout,
            })

    for user_id_str, bet_amount in losers.items():
        bet_amount = int(bet_amount)
        refund = 0

        if has_insurance(state, int(user_id_str)):
            refund = int(round(bet_amount * INSURANCE_REFUND_RATIO))
            add_balance(state, int(user_id_str), refund)
            set_insurance(state, int(user_id_str), False)

        record_loss(state, int(user_id_str), bet_amount - refund)
        results["bet_losers"].append({
            "user_id": int(user_id_str),
            "bet": bet_amount,
            "refund": refund,
        })

    for user_id_str in winners.keys():
        set_insurance(state, int(user_id_str), False)

    return results