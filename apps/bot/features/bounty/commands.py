import discord
from discord import Interaction, Member, app_commands
from discord.ext import commands

from apps.bot.features.betting.service import add_balance, get_balance, load_bets, save_bets
from apps.bot.features.bounty.service import all_bounties, clear_bounty, get_bounty, set_bounty


class Bounty(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="bounty", description="Place a bounty on a player")
    async def bounty(self, interaction: Interaction, user: Member, amount: int) -> None:
        if interaction.user.id == user.id:
            await interaction.response.send_message("You cannot place a bounty on yourself.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.", ephemeral=True)
            return

        state = load_bets()
        balance = get_balance(state, interaction.user.id)
        if balance < amount:
            await interaction.response.send_message("Not enough coins.", ephemeral=True)
            return

        add_balance(state, interaction.user.id, -amount)
        save_bets(state)
        set_bounty(user.id, interaction.user.id, amount)

        embed = discord.Embed(
            title="🎯 Bounty Placed",
            description=f"**{user.display_name}** now has a **{amount}** coin bounty.",
            color=discord.Color.orange(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bounties", description="Show active bounties")
    async def bounties(self, interaction: Interaction) -> None:
        rows = all_bounties()
        if not rows:
            await interaction.response.send_message("No active bounties.", ephemeral=True)
            return

        guild = interaction.guild
        lines = []
        for user_id, payload in rows.items():
            member = guild.get_member(int(user_id)) if guild else None
            name = member.display_name if member else str(user_id)
            lines.append(f"**{name}** — {payload['amount']}")

        embed = discord.Embed(title="🎯 Active Bounties", description="\n".join(lines), color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clearbounty", description="Clear a bounty manually")
    async def clearbounty(self, interaction: Interaction, user: Member) -> None:
        clear_bounty(user.id)
        await interaction.response.send_message(f"Cleared bounty on **{user.display_name}**.", ephemeral=True)

    @app_commands.command(name="claimbounty", description="Manually claim a bounty if target lost")
    async def claimbounty(self, interaction: Interaction, user: Member) -> None:
        bounty = get_bounty(user.id)
        if not bounty:
            await interaction.response.send_message("No active bounty on that user.", ephemeral=True)
            return

        state = load_bets()
        add_balance(state, interaction.user.id, int(bounty["amount"]))
        save_bets(state)
        clear_bounty(user.id)

        embed = discord.Embed(
            title="💰 Bounty Claimed",
            description=f"{interaction.user.mention} claimed **{bounty['amount']}** coins for **{user.display_name}**",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bounty(bot))