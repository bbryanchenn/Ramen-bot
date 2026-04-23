import random

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.features.betting.constants import MAX_BET, MAX_GAMBLE
from apps.bot.features.betting.payout import settle_match
from apps.bot.features.betting.service import (
    add_balance,
    bets_locked,
    clear_current_bets,
    ensure_user,
    get_balance,
    get_pool_totals,
    has_insurance,
    load_bets,
    lock_bets,
    place_bet,
    save_bets,
    set_current_match,
    set_insurance,
)
from apps.bot.features.titles.service import get_equipped_title_name


class Betting(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def _display_name(self, guild: discord.Guild | None, user_id: int) -> str:
        member = guild.get_member(user_id) if guild else None
        base = member.display_name if member else str(user_id)
        title = get_equipped_title_name(user_id)
        return f"{base} [{title}]" if title else base

    @app_commands.command(name="balance", description="Show your coin balance")
    async def balance(self, interaction: Interaction) -> None:
        state = load_bets()
        ensure_user(state, interaction.user.id)
        save_bets(state)

        bal = get_balance(state, interaction.user.id)
        insured = has_insurance(state, interaction.user.id)
        title = get_equipped_title_name(interaction.user.id)

        stats = state.get("stats", {}).get(str(interaction.user.id), {})
        profit = int(stats.get("profit", 0))
        wins = int(stats.get("wins", 0))
        losses = int(stats.get("losses", 0))

        embed = discord.Embed(
            title="💰 Balance",
            color=discord.Color.gold(),
        )
        embed.add_field(name="Coins", value=str(bal), inline=True)
        embed.add_field(name="Insurance", value="✅ Active" if insured else "❌ None", inline=True)
        embed.add_field(name="Title", value=title or "None", inline=True)
        embed.add_field(name="Profit", value=str(profit), inline=True)
        embed.add_field(name="Bet Wins", value=str(wins), inline=True)
        embed.add_field(name="Bet Losses", value=str(losses), inline=True)
        embed.set_footer(text=interaction.user.display_name)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="baltop", description="Show the top 10 richest users")
    async def baltop(self, interaction: Interaction) -> None:
        state = load_bets()
        balances = state.get("balances", {})

        top_entries: list[tuple[int, int]] = []
        for user_id_str, amount in balances.items():
            try:
                user_id = int(user_id_str)
                coins = int(amount)
            except (TypeError, ValueError):
                continue
            top_entries.append((user_id, coins))

        if not top_entries:
            await interaction.response.send_message("No balances found yet.", ephemeral=False)
            return

        top_entries.sort(key=lambda entry: entry[1], reverse=True)
        top_10 = top_entries[:10]

        guild = interaction.guild
        lines = [
            f"**{idx}.** {self._display_name(guild, user_id)} - **{coins}** coins"
            for idx, (user_id, coins) in enumerate(top_10, start=1)
        ]

        embed = discord.Embed(
            title="🏆 Coin Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"Showing top {len(top_10)} users")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bet", description="Bet on blue or red")
    @app_commands.describe(team="blue or red", amount="How much to bet")
    async def bet(self, interaction: Interaction, team: str, amount: int) -> None:
        state = load_bets()
        ensure_user(state, interaction.user.id)

        if amount > MAX_BET:
            await interaction.response.send_message(f"Max bet is {MAX_BET}.", ephemeral=True)
            return

        ok, message = place_bet(state, interaction.user.id, team, amount)
        if not ok:
            await interaction.response.send_message(message, ephemeral=True)
            return

        save_bets(state)
        blue_total, red_total = get_pool_totals(state)

        embed = discord.Embed(
            title="🎯 Bet Placed",
            description=message,
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Blue Pool", value=str(blue_total), inline=True)
        embed.add_field(name="Red Pool", value=str(red_total), inline=True)
        embed.add_field(name="Your Balance", value=str(get_balance(state, interaction.user.id)), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="insurance", description="Protect your next losing bet with a 50% refund")
    async def insurance(self, interaction: Interaction) -> None:
        state = load_bets()
        ensure_user(state, interaction.user.id)
        set_insurance(state, interaction.user.id, True)
        save_bets(state)

        embed = discord.Embed(
            title="🛡️ Insurance Activated",
            description="Your next losing bet will refund 50%.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="allin", description="Bet your entire balance on blue or red")
    @app_commands.describe(team="blue or red")
    async def allin(self, interaction: Interaction, team: str) -> None:
        state = load_bets()
        ensure_user(state, interaction.user.id)
        balance = get_balance(state, interaction.user.id)

        if balance <= 0:
            await interaction.response.send_message("You have no coins.", ephemeral=True)
            return

        ok, message = place_bet(state, interaction.user.id, team, balance)
        if not ok:
            await interaction.response.send_message(message, ephemeral=True)
            return

        save_bets(state)

        embed = discord.Embed(
            title="💀 ALL IN",
            description=f"All in on **{team.title()}** with **{balance}** coins.",
            color=discord.Color.red(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="gamble", description="50/50 gamble your coins")
    @app_commands.describe(amount="How much to gamble")
    async def gamble(self, interaction: Interaction, amount: int) -> None:
        state = load_bets()
        ensure_user(state, interaction.user.id)

        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.", ephemeral=True)
            return

        if amount > MAX_GAMBLE:
            await interaction.response.send_message(f"Max gamble is {MAX_GAMBLE}.", ephemeral=True)
            return

        balance = get_balance(state, interaction.user.id)
        if amount > balance:
            await interaction.response.send_message("You do not have enough coins.", ephemeral=True)
            return

        win = random.random() < 0.5
        delta = amount if win else -amount
        new_balance = add_balance(state, interaction.user.id, delta)
        save_bets(state)

        embed = discord.Embed(
            title="🎰 Gamble",
            color=discord.Color.green() if win else discord.Color.red(),
        )
        embed.add_field(name="Result", value=f"{'Won' if win else 'Lost'} {amount}", inline=True)
        embed.add_field(name="New Balance", value=str(new_balance), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="betstatus", description="Show current betting pools")
    async def betstatus(self, interaction: Interaction) -> None:
        state = load_bets()
        blue_total, red_total = get_pool_totals(state)
        locked = bets_locked(state)

        embed = discord.Embed(
            title="📊 Bet Status",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Blue Pool", value=str(blue_total), inline=True)
        embed.add_field(name="Red Pool", value=str(red_total), inline=True)
        embed.add_field(name="Locked", value="✅" if locked else "❌", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="lockbets", description="Lock betting for the current match")
    async def lockbets(self, interaction: Interaction) -> None:
        state = load_bets()
        lock_bets(state)
        save_bets(state)

        embed = discord.Embed(
            title="🔒 Bets Locked",
            color=discord.Color.orange(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="winner", description="Set the winner and settle bets")
    @app_commands.describe(team="blue or red")
    async def winner(self, interaction: Interaction, team: str) -> None:
        team = team.lower()
        if team not in ("blue", "red"):
            await interaction.response.send_message("Winner must be blue or red.", ephemeral=True)
            return

        state = load_bets()

        salt_value = 0
        try:
            from apps.bot.features.salt.service import get_salt_value
            salt_value = get_salt_value()
        except Exception:
            salt_value = 0

        result = settle_match(state, team, salt_value)
        try:
            from apps.bot.features.history.service import add_match
            from apps.bot.features.voting.service import get_active_vote
            from apps.bot.features.events.service import get_event

            current_match = state.get("current_match", {})
            event = get_event()

            add_match({
                "winner": team,
                "salt": salt_value,
                "blue_team": current_match.get("blue_team", []),
                "red_team": current_match.get("red_team", []),
                "mvp": None,
                "diff": None,
                "event": event["type"] if event else None,
            })
        except Exception:
            pass
        save_bets(state)

        guild = interaction.guild

        embed = discord.Embed(
            title=f"🏁 {team.title()} Team Wins",
            color=discord.Color.blue() if team == "blue" else discord.Color.red(),
        )
        embed.add_field(
            name="Salt Multiplier",
            value=f"x{result['multiplier']:.1f}",
            inline=True,
        )
        embed.add_field(
            name="Blue Pool",
            value=str(result["blue_total"]),
            inline=True,
        )
        embed.add_field(
            name="Red Pool",
            value=str(result["red_total"]),
            inline=True,
        )

        if result["player_rewards"]:
            player_lines = [
                f"+{entry['reward']} {self._display_name(guild, entry['user_id'])}"
                for entry in result["player_rewards"]
            ]
            embed.add_field(
                name="🎮 Player Rewards",
                value="\n".join(player_lines[:10]),
                inline=False,
            )

        if result["bet_winners"]:
            winner_lines = [
                f"{self._display_name(guild, entry['user_id'])}: {entry['payout']} 🤑"
                for entry in result["bet_winners"]
            ]
            embed.add_field(
                name="🎲 Bet Winners",
                value="\n".join(winner_lines[:10]),
                inline=False,
            )
        else:
            embed.add_field(name="🎲 Bet Winners", value="No winning bets.", inline=False)

        if result["bet_losers"]:
            loser_lines = []
            for entry in result["bet_losers"][:10]:
                name = self._display_name(guild, entry["user_id"])
                if entry["refund"] > 0:
                    loser_lines.append(f"{name}: lost {entry['bet']} → refund {entry['refund']}")
                else:
                    loser_lines.append(f"{name}: lost {entry['bet']}")
            embed.add_field(
                name="💀 Bet Losers",
                value="\n".join(loser_lines),
                inline=False,
            )
        else:
            embed.add_field(name="💀 Bet Losers", value="No losing bets.", inline=False)

        clear_current_bets(state)
        save_bets(state)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="resetmatchbets", description="Clear current bets and match state")
    async def resetmatchbets(self, interaction: Interaction) -> None:
        state = load_bets()
        clear_current_bets(state)
        save_bets(state)

        embed = discord.Embed(
            title="🧹 Match Bets Reset",
            color=discord.Color.orange(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setmatchteams", description="Save current generated teams for betting lockouts")
    async def setmatchteams(self, interaction: Interaction) -> None:
        teams_cog = self.bot.get_cog("Teams")
        if teams_cog is None or not hasattr(teams_cog, "last_result"):
            await interaction.response.send_message("No saved teams found.", ephemeral=True)
            return

        last_result = getattr(teams_cog, "last_result", None)
        if not last_result:
            await interaction.response.send_message("No saved teams found.", ephemeral=True)
            return

        teams = last_result.get("teams", [])
        if len(teams) < 2:
            await interaction.response.send_message("Need at least 2 saved teams.", ephemeral=True)
            return

        blue_ids = [player["id"] for player in teams[0].values()]
        red_ids = [player["id"] for player in teams[1].values()]

        state = load_bets()
        set_current_match(state, blue_ids, red_ids)
        save_bets(state)

        embed = discord.Embed(
            title="✅ Match Teams Saved",
            description="Blue and Red teams are now locked in for betting.",
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clearbets", description="Clear your current bet and get refunded if bets are not locked")
    async def clearbets(self, interaction: Interaction) -> None:
        state = load_bets()

        if bets_locked(state):
            await interaction.response.send_message(
                "Bets are already locked.",
                ephemeral=True,
            )
            return

        user_id = str(interaction.user.id)

        blue_bets = state["current_bets"].get("blue", {})
        red_bets = state["current_bets"].get("red", {})

        refund = 0
        cleared_team = None

        if user_id in blue_bets:
            refund = int(blue_bets.pop(user_id))
            cleared_team = "Blue"
        elif user_id in red_bets:
            refund = int(red_bets.pop(user_id))
            cleared_team = "Red"

        if refund <= 0:
            await interaction.response.send_message(
                "You have no active bet.",
                ephemeral=True,
            )
            return

        new_balance = add_balance(state, interaction.user.id, refund)
        set_insurance(state, interaction.user.id, False)
        save_bets(state)

        embed = discord.Embed(
            title="🧹 Bet Cleared",
            description=f"Removed your **{cleared_team}** bet and refunded **{refund}** coins.",
            color=discord.Color.orange(),
        )
        embed.add_field(name="New Balance", value=str(new_balance), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="givecoins", description="Admin command to give coins to a user")
    @app_commands.describe(user="The user to give coins to", amount="How many coins to give")
    async def givecoins(self, interaction: Interaction, user: discord.User, amount: int
    ) -> None:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        state = load_bets()
        ensure_user(state, user.id)
        new_balance = add_balance(state, user.id, amount)
        save_bets(state)

        embed = discord.Embed(
            title="💸 Coins Given",
            description=f"Gave **{amount}** coins to {user.mention}.",
            color=discord.Color.green(),
        )
        embed.add_field(name="New Balance", value=str(new_balance), inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Betting(bot))