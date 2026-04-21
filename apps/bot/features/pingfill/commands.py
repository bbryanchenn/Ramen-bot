import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.features.pingfill.service import find_fill_candidates


class PingFill(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="pingfill", description="DM online Fill players if lobby is short")
    @app_commands.describe(needed="Override how many more players are needed")
    async def pingfill(self, interaction: Interaction, needed: int | None = None) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        lobby_cog = self.bot.get_cog("Lobby")
        if lobby_cog is None:
            await interaction.response.send_message("Lobby system is not loaded.", ephemeral=True)
            return

        lobby_ids = {
            user_id
            for user_id, player in lobby_cog.players.items()
            if player.get("in_lobby", False)
        }
        current_size = len(lobby_ids)

        if needed is None:
            needed = max(0, 10 - current_size)

        if needed <= 0:
            await interaction.response.send_message("Lobby is already full enough.", ephemeral=True)
            return

        candidates, error = find_fill_candidates(guild, lobby_ids)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        if not candidates:
            await interaction.response.send_message(
                f"No online Fill players found. Need {needed} more.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        sent = 0
        failed = 0

        message = (
            f"Inhouse is short **{needed}** player(s) right now.\n"
            f"We currently have **{current_size}/10** in lobby.\n"
            f"If you're down, hop in and use `/join`."
        )

        for member in candidates:
            try:
                await member.send(message)
                sent += 1
            except discord.Forbidden:
                failed += 1
            except discord.HTTPException:
                failed += 1

        embed = discord.Embed(
            title="📢 Ping Fill",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Need", value=str(needed), inline=True)
        embed.add_field(name="DMs Sent", value=str(sent), inline=True)
        embed.add_field(name="Failed", value=str(failed), inline=True)

        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PingFill(bot))