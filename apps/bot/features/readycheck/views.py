import discord

from apps.bot.features.readycheck.service import (
    all_ready,
    get_missing_players,
    get_ready_check,
    mark_ready,
    mark_unready,
    ready_count,
    total_count,
)


def build_ready_embed(guild: discord.Guild) -> discord.Embed:
    state = get_ready_check(guild.id)

    if not state:
        return discord.Embed(
            title="✅ Ready Check",
            description="No active ready check.",
            color=discord.Color.green(),
        )

    ready = ready_count(guild.id)
    total = total_count(guild.id)
    missing_ids = get_missing_players(guild.id)

    ready_names = []
    for uid in state["ready"]:
        member = guild.get_member(uid)
        ready_names.append(member.display_name if member else str(uid))

    missing_names = []
    for uid in missing_ids:
        member = guild.get_member(uid)
        missing_names.append(member.display_name if member else str(uid))

    embed = discord.Embed(
        title="✅ Ready Check",
        color=discord.Color.green() if all_ready(guild.id) else discord.Color.orange(),
    )
    embed.add_field(name="Ready", value=f"{ready}/{total}", inline=True)
    embed.add_field(name="Status", value="All Ready" if all_ready(guild.id) else "Waiting", inline=True)
    embed.add_field(
        name="Ready Players",
        value="\n".join(ready_names) if ready_names else "None yet",
        inline=False,
    )
    embed.add_field(
        name="Missing",
        value="\n".join(missing_names) if missing_names else "Nobody",
        inline=False,
    )
    return embed


class ReadyCheckView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=180)
        self.guild_id = guild_id

    @discord.ui.button(label="Ready", style=discord.ButtonStyle.green)
    async def ready_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, msg = mark_ready(self.guild_id, interaction.user.id)
        if not ok:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        embed = build_ready_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Unready", style=discord.ButtonStyle.red)
    async def unready_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        ok, msg = mark_unready(self.guild_id, interaction.user.id)
        if not ok:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        embed = build_ready_embed(interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)