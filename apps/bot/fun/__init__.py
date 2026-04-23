import random
import time

import discord
from discord import Interaction, Member, app_commands
from discord.ext import commands

from apps.bot.features.betting.service import add_balance, get_balance, load_bets, save_bets

HEIST_MIN_BALANCE = 500
HEIST_TARGET_MIN_BALANCE = 200
HEIST_MIN_STEAL = 100
HEIST_MAX_STEAL = 1500
HEIST_MIN_PENALTY = 100
HEIST_MAX_PENALTY = 1000
HEIST_COOLDOWN_SECONDS = 1800

HEIST_LAST_USED: dict[int, float] = {}


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="heist", description="Attempt to steal coins from someone")
    async def heist(self, interaction: Interaction, user: Member) -> None:
        attacker_id = interaction.user.id
        target_id = user.id

        if attacker_id == target_id:
            await interaction.response.send_message("You cannot heist yourself.", ephemeral=True)
            return

        if user.bot:
            await interaction.response.send_message("You cannot heist a bot.", ephemeral=True)
            return

        now = time.time()
        last_used = HEIST_LAST_USED.get(attacker_id, 0)
        remaining = int(HEIST_COOLDOWN_SECONDS - (now - last_used))
        if remaining > 0:
            minutes = remaining // 60
            seconds = remaining % 60
            await interaction.response.send_message(
                f"Heist is on cooldown. Try again in {minutes}m {seconds}s.",
                ephemeral=True,
            )
            return

        state = load_bets()

        attacker_balance = get_balance(state, attacker_id)
        target_balance = get_balance(state, target_id)

        if attacker_balance < HEIST_MIN_BALANCE:
            await interaction.response.send_message(
                f"You need at least {HEIST_MIN_BALANCE} coins to attempt a heist.",
                ephemeral=True,
            )
            return

        if target_balance < HEIST_TARGET_MIN_BALANCE:
            await interaction.response.send_message(
                f"{user.display_name} is too broke to heist.",
                ephemeral=True,
            )
            return

        success = random.random() < 0.4 # 
        HEIST_LAST_USED[attacker_id] = now

        if success:
            steal_amount = int(target_balance * random.uniform(0.05, 0.15))
            steal_amount = max(HEIST_MIN_STEAL, steal_amount)
            steal_amount = min(HEIST_MAX_STEAL, steal_amount, target_balance)

            add_balance(state, target_id, -steal_amount)
            new_balance = add_balance(state, attacker_id, steal_amount)
            save_bets(state)

            try:
                from apps.bot.features.salt.service import add_salt
                add_salt(1)
            except Exception:
                pass

            embed = discord.Embed(
                title="🤑 Heist Success",
                description=(
                    f"**{interaction.user.display_name}** stole **{steal_amount}** coins "
                    f"from **{user.display_name}**"
                ),
                color=discord.Color.green(),
            )
            embed.add_field(name="Your New Balance", value=str(new_balance), inline=True)
            embed.add_field(name="Target Balance", value=str(get_balance(state, target_id)), inline=True)
            embed.set_footer(text="+1 salt")

            await interaction.response.send_message(embed=embed)
            return

        penalty = int(attacker_balance * 0.10)
        penalty = max(HEIST_MIN_PENALTY, penalty)
        penalty = min(HEIST_MAX_PENALTY, penalty, attacker_balance)

        add_balance(state, attacker_id, -penalty)
        target_new_balance = add_balance(state, target_id, penalty)
        save_bets(state)

        try:
            from apps.bot.features.salt.service import add_salt
            add_salt(2)
        except Exception:
            pass

        embed = discord.Embed(
            title="🚨 Heist Failed",
            description=(
                f"**{interaction.user.display_name}** got caught and paid "
                f"**{penalty}** coins to **{user.display_name}**"
            ),
            color=discord.Color.red(),
        )
        embed.add_field(name="Your New Balance", value=str(get_balance(state, attacker_id)), inline=True)
        embed.add_field(name="Target New Balance", value=str(target_new_balance), inline=True)
        embed.set_footer(text="+2 salt")

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Fun(bot))