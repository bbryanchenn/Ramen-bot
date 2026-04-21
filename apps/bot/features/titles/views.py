import discord

from apps.bot.features.titles.catalog import TITLE_CATALOG
from apps.bot.features.titles.service import buy_title, equip_title, owns_title
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


class TitleShopView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Not your shop.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Buy High Roller", style=discord.ButtonStyle.primary)
    async def buy_high_roller(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "high_roller")

    @discord.ui.button(label="Buy Bank Lord", style=discord.ButtonStyle.primary)
    async def buy_bank_lord(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "bank_lord")

    @discord.ui.button(label="Buy The Differ", style=discord.ButtonStyle.danger)
    async def buy_the_differ(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._handle(interaction, "the_differ")

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
            