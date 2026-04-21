import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.features.betting.service import load_bets
from apps.bot.features.diffs.service import top_diffs, top_mvps
from apps.bot.features.leaderboard.formatter import format_board


class Leaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _top_balances(self, limit: int = 10) -> list[tuple[int, int]]:
        state = load_bets()
        balances = state.get("balances", {})

        rows = []
        for user_id, amount in balances.items():
            rows.append((int(user_id), int(amount)))

        rows.sort(key=lambda x: x[1], reverse=True)
        return rows[:limit]

    def _top_profit(self, limit: int = 10) -> list[tuple[int, int]]:
        state = load_bets()
        stats = state.get("stats", {})

        rows = []
        for user_id, payload in stats.items():
            rows.append((int(user_id), int(payload.get("profit", 0))))

        rows.sort(key=lambda x: x[1], reverse=True)
        return rows[:limit]

    @app_commands.command(name="leaderboard", description="Show a leaderboard")
    @app_commands.describe(category="coins, profit, diffs, or mvps")
    async def leaderboard(self, interaction: Interaction, category: str = "coins") -> None:
        category = category.lower().strip()

        if category == "coins":
            rows = self._top_balances()
            title = "💰 Coin Leaderboard"
        elif category == "profit":
            rows = self._top_profit()
            title = "📈 Profit Leaderboard"
        elif category == "diffs":
            rows = top_diffs(limit=10)
            title = "💀 Diffboard"
        elif category == "mvps":
            rows = top_mvps(limit=10)
            title = "🏆 MVP Board"
        else:
            await interaction.response.send_message(
                "Invalid category. Use: `coins`, `profit`, `diffs`, or `mvps`.",
                ephemeral=True,
            )
            return

        text = format_board(title, rows, interaction.guild)

        embed = discord.Embed(
            title=title,
            description="\n".join(text.split("\n")[1:]) if "\n" in text else "No data yet.",
            color=discord.Color.blurple(),
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinboard", description="Show the coin leaderboard")
    async def coinboard(self, interaction: Interaction) -> None:
        rows = self._top_balances()
        text = format_board("💰 Coin Leaderboard", rows, interaction.guild)

        embed = discord.Embed(
            title="💰 Coin Leaderboard",
            description="\n".join(text.split("\n")[1:]) if "\n" in text else "No data yet.",
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profitboard", description="Show the profit leaderboard")
    async def profitboard(self, interaction: Interaction) -> None:
        rows = self._top_profit()
        text = format_board("📈 Profit Leaderboard", rows, interaction.guild)

        embed = discord.Embed(
            title="📈 Profit Leaderboard",
            description="\n".join(text.split("\n")[1:]) if "\n" in text else "No data yet.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Leaderboard(bot))