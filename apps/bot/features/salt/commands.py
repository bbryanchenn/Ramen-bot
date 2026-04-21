import discord
from discord import app_commands
from discord.ext import commands

from apps.bot.features.salt.service import (
    get_salt_value,
    add_salt,
    reset_salt,
    get_multiplier
)
from apps.bot.features.salt.labels import salt_label, salt_bar


class Salt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="saltmeter", description="Check current salt level")
    async def salt(self, interaction: discord.Interaction):
        salt = get_salt_value()
        mult = get_multiplier()

        embed = discord.Embed(
            title="🧂 Salt Meter",
            color=0xF39C12,
        )
        embed.add_field(
            name="Salt Level",
            value=f"**{salt}** {salt_bar(salt)}",
            inline=False,
        )
        embed.add_field(
            name="Status",
            value=f"**{salt_label(salt)}**",
            inline=True,
        )
        embed.add_field(
            name="Payout Multiplier",
            value=f"**x{mult:.1f}**",
            inline=True,
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="addsalt", description="Convert gold into salt")
    @app_commands.describe(amount="Gold to convert into salt")
    async def addsalt(self, interaction: discord.Interaction, amount: int):
        from apps.bot.features.betting.service import load_bets, save_bets, get_balance, add_balance

        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.", ephemeral=True)
            return

        state = load_bets()
        balance = get_balance(state, interaction.user.id)

        if amount > balance:
            await interaction.response.send_message("Not enough gold.", ephemeral=True)
            return

        # remove gold
        add_balance(state, interaction.user.id, -amount)
        save_bets(state)

        # convert gold → salt
        gained = max(1, amount // 50)
        new_salt = add_salt(gained)

        await interaction.response.send_message(
            f"🔥 Added **{gained}** salt\n"
            f"New Salt: **{new_salt}** {salt_bar(new_salt)}"
        )

    @app_commands.command(name="resetsalt", description="Reset salt (admin)")
    async def resetsalt(self, interaction: discord.Interaction):
        reset_salt()
        await interaction.response.send_message("Salt reset.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Salt(bot))