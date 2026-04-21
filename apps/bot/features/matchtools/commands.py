import discord
from discord import Interaction, Member, app_commands
from discord.ext import commands

from core.builder.optimizer import build_best_lobby


REROLL_COST = 50
SWAP_COST = 25


class MatchTools(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _format_team(self, team: dict[str, dict], index: int) -> str:
        total = sum(player.get("mmr", 500) for player in team.values())
        lines = [f"Team {index} ({total})"]
        for lane, player in team.items():
            lines.append(f"**{lane}** — {player['name']} ({player.get('mmr', 500)})")
        return "\n".join(lines)

    def _find_player_slot(self, teams: list[dict[str, dict]], user_id: int):
        for team_index, team in enumerate(teams):
            for lane, player in team.items():
                if int(player["id"]) == int(user_id):
                    return team_index, lane, player
        return None

    @app_commands.command(name="reroll", description="Reroll the current lobby into new teams")
    async def reroll(self, interaction: Interaction) -> None:
        lobby_cog = self.bot.get_cog("Lobby")
        teams_cog = self.bot.get_cog("Teams")

        if lobby_cog is None or teams_cog is None:
            await interaction.response.send_message("Lobby/Teams system is not loaded.", ephemeral=True)
            return

        players = [p for p in lobby_cog.players.values() if p.get("in_lobby", False)]
        old_result = getattr(teams_cog, "last_result", None)

        if not old_result:
            await interaction.response.send_message("No current teams to reroll.", ephemeral=True)
            return

        old_mode = int(old_result.get("mode", 2))
        needed = 10 if old_mode == 2 else 15

        if len(players) < needed:
            await interaction.response.send_message(
                f"Need at least {needed} players to reroll {old_mode} teams.",
                ephemeral=True,
            )
            return

        from apps.bot.features.betting.service import load_bets, save_bets, get_balance, add_balance

        state = load_bets()
        balance = get_balance(state, interaction.user.id)
        if balance < REROLL_COST:
            await interaction.response.send_message(
                f"You need {REROLL_COST} coins to reroll.",
                ephemeral=True,
            )
            return

        add_balance(state, interaction.user.id, -REROLL_COST)
        save_bets(state)

        result = build_best_lobby(players, team_count=old_mode)
        if result is None:
            await interaction.response.send_message(
                "Could not generate valid rerolled teams.",
                ephemeral=True,
            )
            return

        teams_cog.last_result = result

        try:
            from apps.bot.features.salt.service import add_salt
            add_salt(2)
        except Exception:
            pass

        embed = discord.Embed(
            title="🔁 Teams Rerolled",
            description=f"{interaction.user.mention} paid **{REROLL_COST}** coins",
            color=discord.Color.orange(),
        )

        for i, team in enumerate(result["teams"], start=1):
            embed.add_field(
                name=f"Team {i}",
                value=self._format_team(team, i),
                inline=False,
            )

        bench = result.get("bench", [])
        if bench:
            bench_text = "\n".join(f"**{p['name']}** ({p.get('mmr', 500)})" for p in bench)
            embed.add_field(name="Bench", value=bench_text, inline=False)

        embed.set_footer(text=f"Balance score: {result.get('score', 'N/A')}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="swap", description="Swap two players between current teams")
    @app_commands.describe(user1="First player", user2="Second player")
    async def swap(self, interaction: Interaction, user1: Member, user2: Member) -> None:
        teams_cog = self.bot.get_cog("Teams")
        if teams_cog is None:
            await interaction.response.send_message("Teams system is not loaded.", ephemeral=True)
            return

        result = getattr(teams_cog, "last_result", None)
        if not result:
            await interaction.response.send_message("No current teams to swap from.", ephemeral=True)
            return

        teams = result.get("teams", [])
        if len(teams) < 2:
            await interaction.response.send_message("Need at least 2 teams to swap players.", ephemeral=True)
            return

        slot1 = self._find_player_slot(teams, user1.id)
        slot2 = self._find_player_slot(teams, user2.id)

        if slot1 is None or slot2 is None:
            await interaction.response.send_message(
                "Both users must be in the current generated teams.",
                ephemeral=True,
            )
            return

        team_index_1, lane1, player1 = slot1
        team_index_2, lane2, player2 = slot2

        if team_index_1 == team_index_2:
            await interaction.response.send_message(
                "Those players are already on the same team.",
                ephemeral=True,
            )
            return

        from apps.bot.features.betting.service import load_bets, save_bets, get_balance, add_balance

        state = load_bets()
        balance = get_balance(state, interaction.user.id)
        if balance < SWAP_COST:
            await interaction.response.send_message(
                f"You need {SWAP_COST} coins to swap players.",
                ephemeral=True,
            )
            return

        add_balance(state, interaction.user.id, -SWAP_COST)
        save_bets(state)

        teams[team_index_1][lane1], teams[team_index_2][lane2] = teams[team_index_2][lane2], teams[team_index_1][lane1]
        teams_cog.last_result = result

        try:
            from apps.bot.features.salt.service import add_salt
            add_salt(1)
        except Exception:
            pass

        embed = discord.Embed(
            title="🔄 Players Swapped",
            description=(
                f"{interaction.user.mention} paid **{SWAP_COST}** coins\n"
                f"Swapped **{user1.display_name}** and **{user2.display_name}**"
            ),
            color=discord.Color.blurple(),
        )

        for i, team in enumerate(teams, start=1):
            embed.add_field(
                name=f"Team {i}",
                value=self._format_team(team, i),
                inline=False,
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MatchTools(bot))