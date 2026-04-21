import discord


def find_fill_candidates(guild: discord.Guild, lobby_ids: set[int]) -> tuple[list[discord.Member], str | None]:
    fill_role = discord.utils.get(guild.roles, name="Fill")
    if fill_role is None:
        return [], "Could not find the Fill role."

    candidates = []
    for member in guild.members:
        if member.bot:
            continue
        if member.id in lobby_ids:
            continue
        if fill_role not in member.roles:
            continue
        if member.status == discord.Status.offline:
            continue

        candidates.append(member)

    return candidates, None