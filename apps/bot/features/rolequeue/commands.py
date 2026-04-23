import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.utils.storage import save_players

VALID_ROLES = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT", "FILL"]


class RoleQueue(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="setroles", description="Set your queued roles")
    async def setroles(self, interaction: Interaction, primary: str, secondary: str | None = None) -> None:
        primary = primary.upper().strip()
        secondary = secondary.upper().strip() if secondary else None

        if primary not in VALID_ROLES:
            await interaction.response.send_message("Invalid primary role.", ephemeral=True)
            return

        if secondary and secondary not in VALID_ROLES:
            await interaction.response.send_message("Invalid secondary role.", ephemeral=True)
            return

        roles = [primary]
        if secondary and secondary != primary:
            roles.append(secondary)

        lobby_cog = self.bot.get_cog("Lobby")
        if lobby_cog is None:
            await interaction.response.send_message("Lobby system is not loaded.", ephemeral=True)
            return

        user_id = interaction.user.id
        player = lobby_cog.players.get(user_id)

        if player:
            player["name"] = interaction.user.display_name
            player["roles"] = roles
        else:
            lobby_cog.players[user_id] = {
                "id": user_id,
                "name": interaction.user.display_name,
                "roles": roles,
                "mmr": 500,
                "riot_id": None,
                "puuid": None,
                "summoner_id": None,
                "ranked_entry": None,
                "manual_rank": False,
                "in_lobby": False,
            }

        save_players(lobby_cog.players)

        embed = discord.Embed(
            title="🎯 Roles Updated",
            description=f"Roles set to: **{', '.join(roles)}**",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RoleQueue(bot))