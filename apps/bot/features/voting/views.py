import discord

from apps.bot.features.voting.service import cast_vote, get_active_vote


class VoteSelect(discord.ui.Select):
    def __init__(self, category: str, options: list[discord.SelectOption]):
        placeholder = "Vote MVP" if category == "mvp" else "Vote Diff"
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=options,
        )
        self.category = category

    async def callback(self, interaction: discord.Interaction) -> None:
        target_id = int(self.values[0])
        ok, message = cast_vote(interaction.user.id, target_id, self.category)

        if ok:
            await interaction.response.send_message(
                f"{self.category.upper()} vote saved.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(message, ephemeral=True)


class VoteView(discord.ui.View):
    def __init__(self, guild: discord.Guild, candidates: list[int]):
        super().__init__(timeout=120)

        options = []
        for user_id in candidates:
            member = guild.get_member(user_id)
            name = member.display_name if member else str(user_id)
            options.append(discord.SelectOption(label=name, value=str(user_id)))

        self.add_item(VoteSelect("mvp", options))
        self.add_item(VoteSelect("diff", options))


def build_vote_view(guild: discord.Guild) -> VoteView | None:
    active = get_active_vote()
    if not active:
        return None
    return VoteView(guild, active["candidates"])