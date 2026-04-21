from discord import Interaction, app_commands
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Check if the bot is alive")
    async def ping(self, interaction: Interaction) -> None:
        await interaction.response.send_message("pong")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Ping(bot))