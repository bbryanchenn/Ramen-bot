import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.features.readycheck.service import (
    all_ready,
    clear_ready_check,
    end_ready_check,
    get_missing_players,
    get_ready_check,
    has_ready_check,
    set_message_refs,
    start_ready_check,
)
from apps.bot.features.readycheck.views import ReadyCheckView, build_ready_embed


class ReadyCheck(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="readycheck", description="Start a ready check for the current lobby")
    async def readycheck(self, interaction: Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        lobby_cog = self.bot.get_cog("Lobby")
        if lobby_cog is None:
            await interaction.response.send_message("Lobby system is not loaded.", ephemeral=True)
            return

        if has_ready_check(guild.id):
            await interaction.response.send_message("There is already an active ready check.", ephemeral=True)
            return

        player_ids = [
            user_id
            for user_id, player in lobby_cog.players.items()
            if player.get("in_lobby", False)
        ]
        if not player_ids:
            await interaction.response.send_message("Lobby is empty.", ephemeral=True)
            return

        start_ready_check(guild.id, player_ids)

        embed = build_ready_embed(guild)
        view = ReadyCheckView(guild.id)

        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        set_message_refs(guild.id, msg.channel.id, msg.id)

    @app_commands.command(name="readystatus", description="Check current ready check status")
    async def readystatus(self, interaction: Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        state = get_ready_check(guild.id)
        if not state or not state.get("is_open"):
            await interaction.response.send_message("No active ready check.", ephemeral=True)
            return

        embed = build_ready_embed(guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="endreadycheck", description="End the current ready check")
    async def endreadycheck(self, interaction: Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        state = end_ready_check(guild.id)
        if not state:
            await interaction.response.send_message("No active ready check.", ephemeral=True)
            return

        missing = get_missing_players(guild.id)
        missing_names = []
        for uid in missing:
            member = guild.get_member(uid)
            missing_names.append(member.display_name if member else str(uid))

        embed = discord.Embed(
            title="🛑 Ready Check Ended",
            color=discord.Color.red() if missing else discord.Color.green(),
        )
        embed.add_field(name="All Ready", value="✅ Yes" if all_ready(guild.id) else "❌ No", inline=True)
        embed.add_field(name="Missing", value="\n".join(missing_names) if missing_names else "Nobody", inline=False)

        clear_ready_check(guild.id)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="readymove", description="Move current teams into Blue/Red VCs if everyone is ready")
    async def readymove(self, interaction: Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        if not has_ready_check(guild.id):
            await interaction.response.send_message("No active ready check.", ephemeral=True)
            return

        if not all_ready(guild.id):
            await interaction.response.send_message("Not everyone is ready yet.", ephemeral=True)
            return

        teams_cog = self.bot.get_cog("Teams")
        if teams_cog is None or not hasattr(teams_cog, "last_result"):
            await interaction.response.send_message("No generated teams found.", ephemeral=True)
            return

        result = getattr(teams_cog, "last_result", None)
        if not result:
            await interaction.response.send_message("No generated teams found.", ephemeral=True)
            return

        teams = result.get("teams", [])
        if len(teams) < 2:
            await interaction.response.send_message("Need at least 2 teams.", ephemeral=True)
            return

        blue_vc_id = None
        red_vc_id = None

        try:
            import os
            blue_vc_id = int(os.getenv("BLUE_VC_ID", "0"))
            red_vc_id = int(os.getenv("RED_VC_ID", "0"))
        except ValueError:
            blue_vc_id = 0
            red_vc_id = 0

        blue_vc = guild.get_channel(blue_vc_id) if blue_vc_id else None
        red_vc = guild.get_channel(red_vc_id) if red_vc_id else None

        if not blue_vc or not red_vc:
            await interaction.response.send_message("Could not find Blue/Red voice channels.", ephemeral=True)
            return

        moved = 0
        for i, team in enumerate(teams[:2]):
            vc = blue_vc if i == 0 else red_vc
            for _, player in team.items():
                member = guild.get_member(player["id"])
                if member:
                    try:
                        await member.move_to(vc)
                        moved += 1
                    except Exception:
                        pass

        embed = discord.Embed(
            title="🎤 Players Moved",
            description=f"Moved **{moved}** player(s) into team voice channels.",
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed)

        clear_ready_check(guild.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReadyCheck(bot))