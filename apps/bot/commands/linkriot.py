from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.views.link_confirm_view import LinkConfirmView

class LinkRiot(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="linkriot",
        description="Link your Riot account through DMs"
    )
    async def linkriot(self, interaction: Interaction, riot_id: str) -> None:
        if "#" not in riot_id:
            await interaction.response.send_message(
                "Use format: `gameName#tagLine`",
                ephemeral=True
            )
            return

        game_name, tag_line = riot_id.split("#", 1)
        game_name = game_name.strip()
        tag_line = tag_line.strip()

        if not game_name or not tag_line:
            await interaction.response.send_message(
                "Use format: `gameName#tagLine`",
                ephemeral=True
            )
            return

        lobby_cog = self.bot.get_cog("Lobby")
        if lobby_cog is None:
            await interaction.response.send_message(
                "Lobby system is not loaded",
                ephemeral=True
            )
            return

        if interaction.user.id not in lobby_cog.players:
            await interaction.response.send_message(
                "Join the lobby first with `/join`",
                ephemeral=True
            )
            return

        view = LinkConfirmView(
            bot=self.bot,
            user_id=interaction.user.id,
            game_name=game_name,
            tag_line=tag_line,
        )

        try:
            await interaction.user.send(
                f"You're linking **{game_name}#{tag_line}**.\nPress **Confirm** to continue.",
                view=view
            )
            await interaction.response.send_message(
                "Check your DMs to confirm your Riot account.",
                ephemeral=True
            )
        except Exception:
            await interaction.response.send_message(
                "I couldn't DM you. Turn on **Allow direct messages from server members** and try again.",
                ephemeral=True
            )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LinkRiot(bot))