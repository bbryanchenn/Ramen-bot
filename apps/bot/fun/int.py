import discord
import random
from discord import Interaction, app_commands
from discord.ext import commands

INT_LINES = [
    "ran it down mid 💀",
    "is limit testing again",
    "forgot minimap exists",
    "thought it was ARAM",
    "is playing for the enemy team",
    "just discovered death is permanent",
    "locked in and instantly regretted it",
]

class Int(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="int", description="Call out someone for inting")
    async def int(self, interaction: Interaction, user: discord.Member | None = None) -> None:
        target = user or interaction.user
        line = random.choice(INT_LINES)

        # add salt
        try:
            from apps.bot.features.salt.service import add_salt
            add_salt(1)
        except Exception:
            pass

        embed = discord.Embed(
            title="💀 INT DETECTED",
            description=f"**{target.display_name}** {line}",
            color=discord.Color.red(),
        )

        embed.set_footer(text="+1 salt")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Int(bot))