from discord import Interaction, Member, app_commands
from discord.ext import commands


class MMR(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="setmmr", description="Set a player's MMR")
    async def setmmr(self, interaction: Interaction, user: Member, mmr: int) -> None:
        lobby_cog = self.bot.get_cog("Lobby")
        if lobby_cog is None:
            await interaction.response.send_message("Lobby system is not loaded", ephemeral=True)
            return

        if user.id not in lobby_cog.players:
            await interaction.response.send_message("That user is not in the lobby", ephemeral=True)
            return

        lobby_cog.players[user.id]["mmr"] = mmr
        await interaction.response.send_message(f"Set {user.display_name} to {mmr} MMR")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MMR(bot))