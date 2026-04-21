import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.features.betting.service import load_bets, save_bets
from core.builder.optimizer import build_best_lobby
from core.builder.roles import LANES


class Teams(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.last_result = None
        
    def _format_team(self, team: dict[str, dict], index: int) -> str:
        side_label = "Blue Side" if index == 1 else "Red Side" if index == 2 else f"Team {index}"
        total = sum(player.get("mmr", 500) for player in team.values())
        lines = [f"## {side_label} ({total})"]

        if all(lane in team for lane in LANES):
            for lane in LANES:
                player = team[lane]
                lines.append(f"**{lane}** — {player['name']} ({player.get('mmr', 500)})")
        else:
            for _, player in team.items():
                lines.append(f"**{player['name']}** ({player.get('mmr', 500)})")

        return "\n".join(lines)

    def _format_bench(self, bench: list[dict]) -> str:
        if not bench:
            return ""

        lines = ["## Bench"]
        for player in bench:
            lines.append(f"**{player['name']}** ({player.get('mmr', 500)})")
        return "\n".join(lines)

    @app_commands.command(name="teams", description="Generate balanced teams from the current lobby")
    @app_commands.describe(team_count="Number of teams to build")
    async def teams(self, interaction: Interaction, team_count: int = 2) -> None:
        lobby_cog = self.bot.get_cog("Lobby")
        if lobby_cog is None:
            await interaction.response.send_message("Lobby system is not loaded.", ephemeral=True)
            return

        raw_players = [p for p in lobby_cog.players.values() if p.get("in_lobby", False)]
        if not raw_players:
            await interaction.response.send_message("Lobby is empty.", ephemeral=True)
            return

        if team_count not in (2, 3):
            await interaction.response.send_message("Only 2 or 3 teams are supported.", ephemeral=True)
            return

        players = []
        for player in raw_players:
            players.append({
                "id": player["id"],
                "name": player["name"],
                "roles": [role.upper() for role in player.get("roles", [])],
                "mmr": player.get("mmr", 500),
                "riot_id": player.get("riot_id"),
                "manual_rank": player.get("manual_rank", False),
            })

        await interaction.response.defer()

        small_lobby_mode = len(players) < 10
        if small_lobby_mode:
            sorted_players = sorted(players, key=lambda p: p.get("mmr", 500), reverse=True)
            blue_team = {}
            red_team = {}

            for index, player in enumerate(sorted_players):
                slot = f"P{(index // 2) + 1}"
                if index % 2 == 0:
                    blue_team[slot] = player
                else:
                    red_team[slot] = player

            result = {
                "teams": [blue_team, red_team],
                "mode": 2,
                "score": None,
            }
        else:
            result = build_best_lobby(players, team_count=team_count)
            if result is None:
                await interaction.followup.send(
                    "Could not build valid teams. Make sure the lobby has enough lane coverage.",
                    ephemeral=True,
                )
                return

        self.last_result = result

        teams = result["teams"]
        bench = result.get("bench", [])
        score = result.get("score")

        state = load_bets()
        state.setdefault("current_match", {"blue_team": [], "red_team": [], "bets_locked": False})
        state["current_match"].setdefault("bets_locked", False)
        state["current_match"]["blue_team"] = [int(player["id"]) for player in teams[0].values()]
        state["current_match"]["red_team"] = [int(player["id"]) for player in teams[1].values()]
        save_bets(state)

        embed = discord.Embed(
            title="🧩 Teams Generated",
            color=discord.Color.blurple(),
        )

        for i, team in enumerate(teams, start=1):
            side_label = "Blue Side" if i == 1 else "Red Side" if i == 2 else f"Team {i}"
            embed.add_field(
                name=f"{side_label} ({len(team)} players)",
                value=self._format_team(team, i),
                inline=False,
            )

        bench_block = self._format_bench(bench)
        if bench_block:
            embed.add_field(name="Bench", value=bench_block, inline=False)

        if score is not None:
            embed.add_field(name="Balance Score", value=str(score), inline=False)

        guild = interaction.guild
        if guild is None:
            await interaction.followup.send(embed=embed)
            return

        blue_vc = guild.get_channel(1463801385777627241)  # Replace with actual Blue VC ID
        red_vc = guild.get_channel(1462644484985716909)  # Replace with actual Red VC ID

        moved_count = 0
        if blue_vc and red_vc:
            for i, team in enumerate(teams[:2]):
                vc = blue_vc if i == 0 else red_vc

                for _, player in team.items():
                    member = guild.get_member(player["id"])
                    if member and member.voice:
                        try:
                            await member.move_to(vc)
                            moved_count += 1
                        except Exception:
                            pass

        if moved_count > 0:
            embed.set_footer(text=f"Moved {moved_count} player(s) to team voice channels.")

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Teams(bot))