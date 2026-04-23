import discord

from apps.bot.features.titles.catalog import TITLE_CATALOG
from apps.bot.features.titles.service import (
    buy_title,
    buy_custom_title,
    equip_title,
    owns_title,
)
from apps.bot.features.betting.service import load_bets, get_balance


def build_title_embed(user_id: int) -> discord.Embed:
    balance = get_balance(load_bets(), user_id)

    embed = discord.Embed(
        title="🏷️ Title Shop",
        description="Buy a title and flex on the server.",
    )

    for key, item in TITLE_CATALOG.items():
        owned = " ✅ Owned" if owns_title(user_id, key) else ""
        embed.add_field(
            name=f"{item['name']} — {item['price']} coins{owned}",
            value=item["description"],
            inline=False,
        )

    embed.set_footer(text=f"Your balance: {balance} coins")
    return embed


class CustomTitleModal(discord.ui.Modal):
    custom_text = discord.ui.TextInput(
        label="Custom Title",
        placeholder="Enter your custom title (max 50 chars)",
        max_length=50,
        required=True,
    )

    def __init__(self, user_id: int, parent_view=None):
        super().__init__(title="Custom Title")
        self.user_id = user_id
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        title_text = str(self.custom_text.value).strip()
        ok, msg = buy_custom_title(self.user_id, title_text)
        await interaction.response.send_message(msg, ephemeral=True)

        if ok and self.parent_view and self.parent_view.message:
            embed = build_title_embed(self.user_id)
            await self.parent_view.message.edit(embed=embed, view=self.parent_view)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if interaction.response.is_done():
            await interaction.followup.send(f"Custom title failed: {error}", ephemeral=True)
        else:
            await interaction.response.send_message(f"Custom title failed: {error}", ephemeral=True)


class TitleShopView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your shop.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Buy Ionia Soldier", style=discord.ButtonStyle.primary)
    async def buy_ionia_soldier(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "ionia_soldier")

    @discord.ui.button(label="Buy Bank Lord", style=discord.ButtonStyle.primary)
    async def buy_bank_lord(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "bank_lord")

    @discord.ui.button(label="Buy The Goon King", style=discord.ButtonStyle.danger)
    async def buy_the_goon_king(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "the_goon_king")

    @discord.ui.button(label="Buy Custom Title", style=discord.ButtonStyle.success)
    async def buy_custom_title_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CustomTitleModal(self.user_id, self))

    async def _handle(self, interaction: discord.Interaction, title_key: str):
        if owns_title(self.user_id, title_key):
            ok, msg = equip_title(self.user_id, title_key)
        else:
            ok, msg = buy_title(self.user_id, title_key)

        embed = build_title_embed(self.user_id)

        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
            await interaction.message.edit(embed=embed, view=self)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
            await interaction.message.edit(embed=embed, view=self)
            