import discord
from discord import Interaction, Member, app_commands
from discord.ext import commands

from apps.bot.features.betting.service import add_balance, get_balance, load_bets, save_bets
from apps.bot.features.bounty.service import all_bounties, clear_bounty, get_bounty, set_bounty


class BountyClaimApprovalView(discord.ui.View):
    def __init__(self, target_id: int, claimant_id: int, setter_id: int, amount: int) -> None:
        super().__init__(timeout=300)
        self.target_id = int(target_id)
        self.claimant_id = int(claimant_id)
        self.setter_id = int(setter_id)
        self.amount = int(amount)
        self.resolved = False

    async def interaction_check(self, interaction: Interaction) -> bool:
        user = interaction.user
        is_setter = user.id == self.setter_id
        has_mod_power = bool(user.guild_permissions.manage_guild)

        if not (is_setter or has_mod_power):
            await interaction.response.send_message(
                "Only the bounty setter (or a server manager) can approve this claim.",
                ephemeral=True,
            )
            return False

        return True

    async def _disable_all(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

    @discord.ui.button(label="Approve Claim", style=discord.ButtonStyle.green)
    async def approve(self, interaction: Interaction, button: discord.ui.Button) -> None:
        if self.resolved:
            await interaction.response.send_message("This claim has already been resolved.", ephemeral=True)
            return

        bounty = get_bounty(self.target_id)
        if not bounty:
            await interaction.response.send_message("This bounty is no longer active.", ephemeral=True)
            await self._disable_all()
            self.stop()
            return

        # Re-validate key fields to prevent stale or tampered claim approvals.
        if int(bounty.get("setter_id", 0)) != self.setter_id or int(bounty.get("amount", 0)) != self.amount:
            await interaction.response.send_message(
                "Bounty details changed. Please run `/claimbounty` again.",
                ephemeral=True,
            )
            await self._disable_all()
            self.stop()
            return

        state = load_bets()
        add_balance(state, self.claimant_id, self.amount)
        save_bets(state)
        clear_bounty(self.target_id)

        self.resolved = True
        await self._disable_all()

        guild = interaction.guild
        claimant_member = guild.get_member(self.claimant_id) if guild else None
        claimant_name = claimant_member.mention if claimant_member else f"<@{self.claimant_id}>"

        await interaction.response.edit_message(
            content=f"✅ Approved: {claimant_name} received **{self.amount}** bounty coins.",
            view=self,
        )
        self.stop()

    @discord.ui.button(label="Deny Claim", style=discord.ButtonStyle.red)
    async def deny(self, interaction: Interaction, button: discord.ui.Button) -> None:
        if self.resolved:
            await interaction.response.send_message("This claim has already been resolved.", ephemeral=True)
            return

        self.resolved = True
        await self._disable_all()
        await interaction.response.edit_message(content="❌ Claim denied. Bounty remains active.", view=self)
        self.stop()


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

        amount = int(bounty["amount"])
        setter_id = int(bounty["setter_id"])

        if interaction.user.id == user.id:
            await interaction.response.send_message("You cannot claim a bounty on yourself.", ephemeral=True)
            return

        guild = interaction.guild
        setter_member = guild.get_member(setter_id) if guild else None
        setter_name = setter_member.mention if setter_member else f"<@{setter_id}>"

        view = BountyClaimApprovalView(
            target_id=user.id,
            claimant_id=interaction.user.id,
            setter_id=setter_id,
            amount=amount,
        )

        embed = discord.Embed(
            title="🧾 Bounty Claim Pending Approval",
            description=(
                f"{interaction.user.mention} requested to claim **{amount}** coins "
                f"for **{user.display_name}**."
            ),
            color=discord.Color.gold(),
        )
        embed.add_field(name="Approver", value=f"{setter_name} or a server manager", inline=False)
        embed.set_footer(text="The claim is only paid after approval.")

        await interaction.response.send_message(content=setter_name, embed=embed, view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Bounty(bot))