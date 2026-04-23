import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.features.titles.service import get_equipped_title_name
from apps.bot.features.titles.views import TitleShopView, build_title_embed, CustomTitleModal


class Titles(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="title", description="Open the title shop")
    async def title(self, interaction: Interaction) -> None:
        embed = build_title_embed(interaction.user.id)
        view = TitleShopView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        view.message = await interaction.original_response()

    @app_commands.command(name="mytitle", description="Show your equipped title")
    async def mytitle(self, interaction: Interaction) -> None:
        title = get_equipped_title_name(interaction.user.id)
        if not title:
            await interaction.response.send_message("You have no equipped title.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🏷️ Equipped Title",
            description=f"**{title}**",
            color=discord.Color.purple(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="editcustom", description="Edit your custom title")
    async def editcustom(self, interaction: Interaction) -> None:
        await interaction.response.send_modal(CustomTitleModal(interaction.user.id))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Titles(bot))