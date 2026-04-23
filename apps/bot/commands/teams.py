import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.features.betting.service import load_bets, save_bets
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

    @app_commands.command(name="teams", description="Form teams from players who joined /joinblue and /joinred")
    async def teams(self, interaction: Interaction) -> None:
        lobby_cog = self.bot.get_cog("Lobby")
        if lobby_cog is None:
            await interaction.response.send_message("Lobby system is not loaded.", ephemeral=True)
            return

        state = load_bets()
        state.setdefault("current_match", {"blue_team": [], "red_team": [], "bets_locked": False})
        
        blue_team_ids = state["current_match"].get("blue_team", [])
        red_team_ids = state["current_match"].get("red_team", [])

        if not blue_team_ids and not red_team_ids:
            await interaction.response.send_message(
                "No teams assigned. Use `/joinblue` or `/joinred` to assign players to teams.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        # Build team dicts with players from lobby
        blue_team = {}
        red_team = {}

        for user_id in blue_team_ids:
            player = lobby_cog.players.get(user_id)
            if player:
                blue_team[f"P{len(blue_team) + 1}"] = {
                    "id": player["id"],
                    "name": player["name"],
                    "roles": player.get("roles", []),
                    "mmr": player.get("mmr", 500),
                }

        for user_id in red_team_ids:
            player = lobby_cog.players.get(user_id)
            if player:
                red_team[f"P{len(red_team) + 1}"] = {
                    "id": player["id"],
                    "name": player["name"],
                    "roles": player.get("roles", []),
                    "mmr": player.get("mmr", 500),
                }

        teams = [blue_team, red_team]
        save_bets(state)

        embed = discord.Embed(
            title="🧩 Teams Set",
            color=discord.Color.blurple(),
        )

        for i, team in enumerate(teams, start=1):
            side_label = "Blue Side" if i == 1 else "Red Side"
            if team:
                embed.add_field(
                    name=f"{side_label} ({len(team)} players)",
                    value=self._format_team(team, i),
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"{side_label}",
                    value="Empty",
                    inline=False,
                )

        guild = interaction.guild
        if guild is None:
            await interaction.followup.send(embed=embed)
            return

        blue_vc = guild.get_channel(1463801385777627241)
        red_vc = guild.get_channel(1462644484985716909)

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