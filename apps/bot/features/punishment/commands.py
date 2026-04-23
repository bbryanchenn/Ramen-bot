import discord
from discord import Interaction, Member, app_commands
from discord.ext import commands

from apps.bot.features.diffs.service import get_diff_count


class Punishment(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="shame", description="Publicly shame a player")
    async def shame(self, interaction: Interaction, user: Member) -> None:
        diffs = get_diff_count(user.id)

        if diffs >= 15:
            label = "💀 Certified Scapegoat"
        elif diffs >= 8:
            label = "🤡 Serial Inter"
        elif diffs >= 3:
            label = "⚠️ Under Investigation by Riot"
        else:
            label = "🙂 Somehow still safe"

        embed = discord.Embed(
            title="📣 Shame Report",
            description=f"**{user.display_name}**\nStatus: **{label}**\nTotal Diffs: **{diffs}**",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="topdiff", description="Show the most shameful player")
    async def topdiff(self, interaction: Interaction) -> None:
        from apps.bot.features.diffs.service import top_diffs

        rows = top_diffs(1)
        if not rows:
            await interaction.response.send_message("No diff data yet.", ephemeral=True)
            return

        user_id, diffs = rows[0]
        member = interaction.guild.get_member(user_id) if interaction.guild else None
        name = member.display_name if member else str(user_id)

        embed = discord.Embed(
            title="💀 Most Wanted",
            description=f"**{name}** leads the diffboard with **{diffs}** diffs.",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Punishment(bot))