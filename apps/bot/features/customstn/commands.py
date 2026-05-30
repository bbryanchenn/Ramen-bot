from __future__ import annotations

from datetime import datetime

import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.features.customstn.service import bind_message, clear_custom_stn, has_active_custom_stn, start_custom_stn
from apps.bot.features.customstn.views import build_time_select_view, build_vote_embed, build_vote_view


class CustomSTN(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _publish_vote(self, interaction: Interaction, start_time: datetime) -> None:
        guild = interaction.guild
        channel = interaction.channel

        if guild is None:
            raise RuntimeError("Use this in a server.")

        if channel is None or not hasattr(channel, "send"):
            raise RuntimeError("Use this in a channel that can send messages.")

        if has_active_custom_stn(guild.id):
            raise RuntimeError("There is already an active custom vote in this server.")

        start_custom_stn(guild.id, getattr(channel, "id", 0), start_time, interaction.user.id)

        view = build_vote_view(guild.id, start_time, interaction.user.id)
        embed = build_vote_embed(guild, start_time, 0)
        try:
            message = await channel.send(embed=embed, view=view)
        except Exception:
            clear_custom_stn(guild.id)
            raise

        bind_message(guild.id, message.id)

    @app_commands.command(name="customstn", description="Post a custom vote that can auto-create a scheduled event")
    @app_commands.checks.has_permissions(administrator=True)
    async def customstn(self, interaction: Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        if interaction.channel is None or not hasattr(interaction.channel, "send"):
            await interaction.response.send_message("Use this in a channel that can send messages.", ephemeral=True)
            return

        if has_active_custom_stn(interaction.guild.id):
            await interaction.response.send_message("There is already an active custom vote in this server.", ephemeral=True)
            return

        view = build_time_select_view(self._publish_vote)
        await interaction.response.send_message(
            "Choose the event start time. I will post the yes-vote message in this channel after you pick one.",
            view=view,
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CustomSTN(bot))
