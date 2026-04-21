def salt_label(salt: int) -> str:
    if salt < 2:
        return "🧊 Calm"
    elif salt < 5:
        return "🌶️ Mild"
    elif salt < 8:
        return "🔥 High"
    else:
        return "💀 CRITICAL"


def salt_bar(salt: int) -> str:
    bars = min(5, salt // 2)
    return "🔥" * bars if bars > 0 else "🧊"