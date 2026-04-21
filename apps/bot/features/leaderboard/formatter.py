from apps.bot.features.titles.service import get_equipped_title_name


def format_name(guild, user_id: int) -> str:
    member = guild.get_member(user_id) if guild else None
    base_name = member.display_name if member else str(user_id)

    title = get_equipped_title_name(user_id)
    if title:
        return f"{base_name} [{title}]"

    return base_name


def medal_prefix(index: int) -> str:
    if index == 1:
        return "🥇"
    if index == 2:
        return "🥈"
    if index == 3:
        return "🥉"
    return f"#{index}"


def format_board(title: str, rows: list[tuple[int, int]], guild) -> str:
    if not rows:
        return f"**{title}**\nNo data yet."

    lines = [f"**{title}**"]

    for i, (user_id, value) in enumerate(rows, start=1):
        name = format_name(guild, user_id)
        prefix = medal_prefix(i)
        lines.append(f"{prefix} {name} — **{value}**")

    return "\n".join(lines)