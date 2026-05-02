import discord


def find_fill_candidates(guild: discord.Guild, lobby_ids: set[int]) -> tuple[list[discord.Member], str | None]:
    fill_role = next((role for role in guild.roles if role.name.strip().lower() == "fill"), None)
    if fill_role is None:
        return [], "Could not find the Fill role."

    clasher_role = next((role for role in guild.roles if role.name.strip().lower() == "clasher"), None)
    if clasher_role is None:
        return [], "Could not find the Clasher role."

    candidates = []
    for member in guild.members:
        if member.bot:
            continue
        if member.id in lobby_ids:
            continue
        if fill_role not in member.roles:
            continue
        if clasher_role not in member.roles:
            continue
        if member.status != discord.Status.online:
            continue
        if member.voice is not None:
            continue

        candidates.append(member)

    return candidates, None