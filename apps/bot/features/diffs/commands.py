import random

import discord
from discord import Interaction, Member, app_commands
from discord.ext import commands

from apps.bot.features.diffs.service import (
    add_diff,
    get_diff_count,
    get_mvp_count,
    random_blame_message,
    top_diffs,
    top_mvps,
)


class Diffs(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="blame", description="Blame someone or let fate decide")
    @app_commands.describe(user="Optional user to blame")
    async def blame(self, interaction: Interaction, user: Member | None = None) -> None:
        if user is not None:
            ok, total = add_diff(user.id)

            if not ok:
                await interaction.response.send_message(
                    f"{user.display_name} just got diffed last game. Pick someone else 💀",
                    ephemeral=True
                )
                return

            try:
                from apps.bot.features.salt.service import add_salt
                add_salt(2)
            except Exception:
                pass

            await interaction.response.send_message(
                f"{user.mention} diff 💀\nTotal diffs: **{total}**"
            )
            return

        lobby_cog = self.bot.get_cog("Lobby")
        if lobby_cog and getattr(lobby_cog, "players", None):
            active_players = [p for p in lobby_cog.players.values() if p.get("in_lobby", False)]
            if not active_players:
                await interaction.response.send_message(random_blame_message())
                return

            player = random.choice(active_players)
            total = add_diff(player["id"])

            try:
                from apps.bot.features.salt.service import add_salt
                add_salt(2)
            except Exception:
                pass

            await interaction.response.send_message(
                f"**{player['name']}** diff 💀\nTotal diffs: **{total}**"
            )
            return

        await interaction.response.send_message(random_blame_message())

    @app_commands.command(name="diffboard", description="Show most blamed players")
    async def diffboard(self, interaction: Interaction) -> None:
        rows = top_diffs(limit=10)
        if not rows:
            await interaction.response.send_message("No diff data yet.")
            return

        guild = interaction.guild

        lines = []
        medals = ["🥇", "🥈", "🥉"]

        for i, (user_id, diffs) in enumerate(rows, start=1):
            member = guild.get_member(user_id) if guild else None
            name = member.display_name if member else str(user_id)
            prefix = medals[i - 1] if i <= 3 else f"#{i}"
            lines.append(f"{prefix} {name} — **{diffs}**")

        embed = discord.Embed(
            title="💀 Diffboard",
            description="\n".join(lines),
            color=0xE74C3C,
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mvpboard", description="Show MVP leaderboard")
    async def mvpboard(self, interaction: Interaction) -> None:
        rows = top_mvps(limit=10)
        if not rows:
            await interaction.response.send_message("No MVP data yet.")
            return

        guild = interaction.guild

        lines = ["🏆 **MVP Board**"]
        medals = ["🥇", "🥈", "🥉"]

        for i, (user_id, mvps) in enumerate(rows, start=1):
            member = guild.get_member(user_id) if guild else None
            name = member.display_name if member else str(user_id)
            prefix = medals[i - 1] if i <= 3 else f"#{i}"
            lines.append(f"{prefix} {name} — **{mvps}**")

        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="playerstats", description="Show a player's diff and MVP counts")
    @app_commands.describe(user="User to inspect")
    async def playerstats(self, interaction: Interaction, user: Member) -> None:
        diffs = get_diff_count(user.id)
        mvps = get_mvp_count(user.id)

        await interaction.response.send_message(
            f"**{user.display_name}**\n"
            f"💀 Diffs: **{diffs}**\n"
            f"🏆 MVPs: **{mvps}**"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Diffs(bot))