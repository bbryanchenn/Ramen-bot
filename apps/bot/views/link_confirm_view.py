import discord
from discord.ui import View, button

from apps.bot.utils.storage import save_players
from apps.bot.views.manual_rank_view import ManualRankView
from core.riot.api import fetch_rank_profile
from core.riot.mmr import entry_to_mmr, format_rank


class LinkConfirmView(View):
    def __init__(self, bot, user_id: int, game_name: str, tag_line: str):
        super().__init__(timeout=60)
        self.bot = bot
        self.user_id = user_id
        self.game_name = game_name
        self.tag_line = tag_line

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your request", ephemeral=True)
            return False
        return True

    async def on_error(self, interaction: discord.Interaction, error: Exception, item) -> None:
        try:
            if interaction.response.is_done():
                await interaction.followup.send(f"Error: {error}", ephemeral=True)
            else:
                await interaction.response.send_message(f"Error: {error}", ephemeral=True)
        except Exception:
            pass

    @button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        profile = await fetch_rank_profile(self.game_name, self.tag_line)

        if not profile:
            await interaction.followup.send("Riot lookup failed.", ephemeral=True)
            return

        if profile.get("error"):
            manual_view = ManualRankView(
                bot=self.bot,
                user_id=self.user_id,
                riot_id=f"{self.game_name}#{self.tag_line}",
                puuid=profile.get("puuid"),
            )
            await interaction.followup.send(
                f"{profile['error']}\n\nPick your rank manually below.",
                view=manual_view,
                ephemeral=True,
            )
            return

        if profile.get("rank_unavailable"):
            manual_view = ManualRankView(
                bot=self.bot,
                user_id=self.user_id,
                riot_id=f"{self.game_name}#{self.tag_line}",
                puuid=profile.get("puuid"),
            )
            await interaction.followup.send(
                "I found your Riot account, but Riot rank lookup failed.\n"
                "Pick your rank manually below.",
                view=manual_view,
                ephemeral=True,
            )
            return

        best = profile.get("best")
        if not best:
            manual_view = ManualRankView(
                bot=self.bot,
                user_id=self.user_id,
                riot_id=f"{self.game_name}#{self.tag_line}",
                puuid=profile.get("puuid"),
            )
            await interaction.followup.send(
                "I found your Riot account, but no ranked queue data was available.\n"
                "Pick your rank manually below.",
                view=manual_view,
                ephemeral=True,
            )
            return

        mmr = entry_to_mmr(best)

        lobby_cog = self.bot.get_cog("Lobby")

        if lobby_cog is None:
            await interaction.followup.send("Lobby system not loaded", ephemeral=True)
            return

        if interaction.user.id not in lobby_cog.players:
            await interaction.followup.send("Join lobby first with /join", ephemeral=True)
            return

        player = lobby_cog.players[interaction.user.id]
        in_lobby = player.get("in_lobby", False)
        player["riot_id"] = f"{self.game_name}#{self.tag_line}"
        player["puuid"] = profile.get("puuid")
        player["summoner_id"] = profile.get("summoner_id")
        player["ranked_entry"] = best
        player["mmr"] = mmr
        player["manual_rank"] = False
        player["in_lobby"] = in_lobby

        button.disabled = True
        self.stop()
        
        save_players(lobby_cog.players)

        await interaction.followup.send(
            f"Linked **{self.game_name}#{self.tag_line}**\n"
            f"Rank: **{format_rank(best)}**\n"
            f"MMR: **{mmr}**",
            ephemeral=True,
        )

    @button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cancelled", ephemeral=True)
        self.stop()