import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.features.titles.service import get_equipped_title_name
from apps.bot.features.voting.service import get_active_vote, has_active_vote, start_vote, tally_votes
from apps.bot.features.voting.views import build_vote_view


class Voting(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="startvote", description="Start post-game MVP/Diff voting from the last teams")
    async def startvote(self, interaction: Interaction) -> None:
        teams_cog = self.bot.get_cog("Teams")
        if teams_cog is None or not hasattr(teams_cog, "last_result"):
            await interaction.response.send_message("No recent teams found.", ephemeral=True)
            return

        last_result = getattr(teams_cog, "last_result", None)
        if not last_result:
            await interaction.response.send_message("No recent teams found.", ephemeral=True)
            return

        teams = last_result.get("teams", [])
        if len(teams) < 2:
            await interaction.response.send_message("Need at least 2 teams to start voting.", ephemeral=True)
            return

        candidates = []
        for team in teams[:2]:
            for player in team.values():
                candidates.append(int(player["id"]))

        start_vote(candidates)
        view = build_vote_view(interaction.guild)

        await interaction.response.send_message(
            "🏆 **Post-Game Voting**\nVote for MVP and Diff below.",
            view=view
        )

    @app_commands.command(name="endvote", description="End voting and tally results")
    async def endvote(self, interaction: Interaction) -> None:
        if not has_active_vote():
            await interaction.response.send_message("No active vote.", ephemeral=True)
            return

        result = tally_votes()
        if not result:
            await interaction.response.send_message("No active vote.", ephemeral=True)
            return

        guild = interaction.guild

        def resolve_name(user_id: int | None) -> str:
            if user_id is None:
                return "None"
            member = guild.get_member(user_id) if guild else None
            return member.display_name if member else str(user_id)

        lines = ["🏁 **Vote Results**"]

        if result["mvp_winner"] is not None:
            mvp_votes = result["mvp_counts"].get(result["mvp_winner"], 0)
            lines.append(f"🏆 MVP: **{resolve_name(result['mvp_winner'])}** ({mvp_votes} votes)")
        else:
            lines.append("🏆 MVP: No votes")

        if result["diff_winner"] is not None:
            diff_votes = result["diff_counts"].get(result["diff_winner"], 0)
            lines.append(f"💀 Diff: **{resolve_name(result['diff_winner'])}** ({diff_votes} votes)")
        else:
            lines.append("💀 Diff: No votes")

        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="votestatus", description="Check active vote status")
    async def votestatus(self, interaction: Interaction) -> None:
        active = get_active_vote()
        if not active or not active.get("is_open"):
            await interaction.response.send_message("No active vote.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"Active vote with **{len(active['candidates'])}** candidates.\n"
            f"MVP votes cast: **{len(active['mvp_votes'])}**\n"
            f"Diff votes cast: **{len(active['diff_votes'])}**",
            ephemeral=True,
        )

    @app_commands.command(name="flex", description="Show off your equipped title")
    async def flex(self, interaction: Interaction) -> None:
        title = get_equipped_title_name(interaction.user.id)
        if not title:
            await interaction.response.send_message(
                "You have no equipped title. Use `/title` first.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"💎 **{interaction.user.display_name}** is flexing **[{title}]**"
        )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Voting(bot))