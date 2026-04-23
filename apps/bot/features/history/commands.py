import discord
from discord import Interaction, Member, app_commands
from discord.ext import commands

from apps.bot.features.history.service import latest_matches, user_matches


class History(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="history", description="Show recent match history")
    async def history(self, interaction: Interaction) -> None:
        rows = latest_matches(10)
        if not rows:
            await interaction.response.send_message("No match history yet.", ephemeral=True)
            return

        guild = interaction.guild
        lines = []
        for match in rows:
            winner = match.get("winner", "?").title()
            mvp = match.get("mvp")
            diff = match.get("diff")
            mvp_name = guild.get_member(mvp).display_name if guild and mvp and guild.get_member(mvp) else "None"
            diff_name = guild.get_member(diff).display_name if guild and diff and guild.get_member(diff) else "None"
            lines.append(
                f"**#{match['id']}** — Winner: **{winner}** | Salt: **{match.get('salt', 0)}** | MVP: **{mvp_name}** | Diff: **{diff_name}**"
            )

        embed = discord.Embed(title="🧾 Match History", description="\n".join(lines), color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userhistory", description="Show a user's recent match history")
    async def userhistory(self, interaction: Interaction, user: Member) -> None:
        rows = user_matches(user.id, 10)
        if not rows:
            await interaction.response.send_message("No history for that user.", ephemeral=True)
            return

        lines = []
        for match in rows:
            winner = match.get("winner", "?").title()
            side = "Blue" if user.id in set(match.get("blue_team", [])) else "Red"
            lines.append(f"**#{match['id']}** — Side: **{side}** | Winner: **{winner}** | Salt: **{match.get('salt', 0)}**")

        embed = discord.Embed(
            title=f"🧾 {user.display_name} Match History",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(History(bot))