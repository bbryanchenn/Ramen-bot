import discord
from discord.ui import Select, View

from apps.bot.utils.storage import save_players
from core.riot.mmr import TIER_BASE, RANK_OFFSET


def manual_rank_to_mmr(tier: str, rank: str) -> int:
    return TIER_BASE[tier] + RANK_OFFSET.get(rank, 0)


class TierSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Iron", value="IRON"),
            discord.SelectOption(label="Bronze", value="BRONZE"),
            discord.SelectOption(label="Silver", value="SILVER"),
            discord.SelectOption(label="Gold", value="GOLD"),
            discord.SelectOption(label="Platinum", value="PLATINUM"),
            discord.SelectOption(label="Emerald", value="EMERALD"),
            discord.SelectOption(label="Diamond", value="DIAMOND"),
            discord.SelectOption(label="Master", value="MASTER"),
            discord.SelectOption(label="Grandmaster", value="GRANDMASTER"),
            discord.SelectOption(label="Challenger", value="CHALLENGER"),
        ]
        super().__init__(
            placeholder="Choose your tier",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        view: ManualRankView = self.view
        view.selected_tier = self.values[0]
        await interaction.response.defer()


class DivisionSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="IV", value="IV"),
            discord.SelectOption(label="III", value="III"),
            discord.SelectOption(label="II", value="II"),
            discord.SelectOption(label="I", value="I"),
        ]
        super().__init__(
            placeholder="Choose your division",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        view: ManualRankView = self.view
        view.selected_rank = self.values[0]
        await interaction.response.defer()


class ManualRankView(View):
    def __init__(self, bot, user_id: int, riot_id: str, puuid: str | None = None):
        super().__init__(timeout=120)
        self.bot = bot
        self.user_id = user_id
        self.riot_id = riot_id
        self.puuid = puuid
        self.selected_tier: str | None = None
        self.selected_rank: str | None = None

        self.add_item(TierSelect())
        self.add_item(DivisionSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your request.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Save Rank", style=discord.ButtonStyle.green)
    async def save_rank(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_tier or not self.selected_rank:
            await interaction.response.send_message(
                "Pick both a tier and division first.",
                ephemeral=True,
            )
            return

        lobby_cog = self.bot.get_cog("Lobby")
        if lobby_cog is None:
            await interaction.response.send_message("Lobby system is not loaded.", ephemeral=True)
            return

        if interaction.user.id not in lobby_cog.players:
            await interaction.response.send_message("Join the lobby first with /join.", ephemeral=True)
            return

        mmr = manual_rank_to_mmr(self.selected_tier, self.selected_rank)

        player = lobby_cog.players[interaction.user.id]
        player["riot_id"] = self.riot_id
        player["puuid"] = self.puuid
        player["summoner_id"] = None
        player["ranked_entry"] = {
            "queueType": "MANUAL",
            "tier": self.selected_tier,
            "rank": self.selected_rank,
            "leaguePoints": 0,
            "wins": 0,
            "losses": 0,
        }
        player["mmr"] = mmr
        player["manual_rank"] = True

        save_players(lobby_cog.players)

        button.disabled = True
        self.stop()

        await interaction.response.send_message(
            f"Saved manual rank: **{self.selected_tier} {self.selected_rank}**\n"
            f"MMR: **{mmr}**",
            ephemeral=False,
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cancelled.", ephemeral=False)
        self.stop()