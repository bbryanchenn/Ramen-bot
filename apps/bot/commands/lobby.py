import discord
from discord import Interaction, app_commands
from discord.ext import commands
from apps.bot.utils.storage import load_players, save_players

from apps.bot.utils.roles import extract_player_roles
from apps.bot.features.betting.service import bets_locked, join_side, leave_sides, load_bets, save_bets

class Lobby(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.players: dict[int, dict] = load_players()

    def _ensure_lobby_player(self, interaction: Interaction) -> dict:
        member = interaction.user
        current_roles = extract_player_roles(member)
        player = self.players.get(member.id)

        if player:
            player["name"] = member.display_name
            player["roles"] = current_roles
            player["in_lobby"] = True
            return player

        player = {
            "id": member.id,
            "name": member.display_name,
            "roles": current_roles,
            "mmr": 500,
            "riot_id": None,
            "puuid": None,
            "summoner_id": None,
            "ranked_entry": None,
            "manual_rank": False,
            "in_lobby": True,
        }
        self.players[member.id] = player
        return player

    @app_commands.command(name="join", description="Join the current inhouse lobby")
    async def join(self, interaction: Interaction) -> None:
        member = interaction.user
        player = self._ensure_lobby_player(interaction)

        save_players(self.players)

        await interaction.response.send_message(
            f"{member.mention} joined the lobby\nRoles: {', '.join(player.get('roles', []))}"
        )

    @app_commands.command(name="leave", description="Leave the current inhouse lobby")
    async def leave(self, interaction: Interaction) -> None:
        player = self.players.get(interaction.user.id)
        if not player or not player.get("in_lobby", False):
            await interaction.response.send_message("You are not in the lobby.", ephemeral=True)
            return

        player["in_lobby"] = False

        state = load_bets()
        leave_sides(state, interaction.user.id)

        save_bets(state)
        save_players(self.players)
        await interaction.response.send_message("You left the lobby.", ephemeral=True)

    @app_commands.command(name="lobby", description="Show current lobby")
    async def lobby(self, interaction: Interaction) -> None:
        active_players = [p for p in self.players.values() if p.get("in_lobby", False)]
        if not active_players:
            await interaction.response.send_message("Lobby is empty")
            return

        lines = []
        for p in active_players:
            lines.append(f"**{p['name']}** — {', '.join(p.get('roles', []))} — MMR {p.get('mmr', 500)}")

        await interaction.response.send_message("\n".join(lines))

    @app_commands.command(name="clearlobby", description="Clear the current lobby")
    async def clearlobby(self, interaction: Interaction) -> None:
        if not hasattr(self, "players") or not self.players:
            await interaction.response.send_message(
                "Lobby is already empty.",
                ephemeral=True
            )
            return

        count = 0
        cleared_ids = []
        for player in self.players.values():
            if player.get("in_lobby", False):
                player["in_lobby"] = False
                cleared_ids.append(int(player["id"]))
                count += 1

        if count == 0:
            await interaction.response.send_message(
                "Lobby is already empty.",
                ephemeral=True,
            )
            return

        state = load_bets()
        for user_id in cleared_ids:
            leave_sides(state, user_id)

        save_bets(state)
        save_players(self.players)

        embed = discord.Embed(
            title="🧹 Lobby Cleared",
            description=f"Removed **{count}** player(s) from the lobby.",
            color=discord.Color.orange(),
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="joinblue", description="Join the Blue team manually")
    async def joinblue(self, interaction: Interaction) -> None:
        self._ensure_lobby_player(interaction)
        state = load_bets()
        user_id = interaction.user.id

        if bets_locked(state):
            await interaction.response.send_message(
                "Match is locked. Cannot change teams.",
                ephemeral=True
            )
            return

        match = join_side(state, user_id, "blue")

        save_players(self.players)
        save_bets(state)

        embed = discord.Embed(
            title="🔵 Joined Blue Team",
            description=f"{interaction.user.mention} is now on **Blue**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Blue Count", value=str(len(match["blue_team"])), inline=True)
        embed.add_field(name="Red Count", value=str(len(match["red_team"])), inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="joinred", description="Join the Red team manually")
    async def joinred(self, interaction: Interaction) -> None:
        self._ensure_lobby_player(interaction)
        state = load_bets()
        user_id = interaction.user.id

        if bets_locked(state):
            await interaction.response.send_message(
                "Match is locked. Cannot change teams.",
                ephemeral=True
            )
            return

        match = join_side(state, user_id, "red")

        save_players(self.players)
        save_bets(state)

        embed = discord.Embed(
            title="🔴 Joined Red Team",
            description=f"{interaction.user.mention} is now on **Red**",
            color=discord.Color.red()
        )
        embed.add_field(name="Blue Count", value=str(len(match["blue_team"])), inline=True)
        embed.add_field(name="Red Count", value=str(len(match["red_team"])), inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Lobby(bot))