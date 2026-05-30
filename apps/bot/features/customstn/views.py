from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

import discord

from apps.bot.features.customstn.service import (
    YES_THRESHOLD,
    abort_event_creation,
    cast_yes_vote,
    clear_custom_stn,
    finish_event_creation,
    get_custom_stn,
    reserve_event_creation,
)


TIME_PRESETS: list[tuple[str, int]] = [
    ("In 30 minutes", 30),
    ("In 1 hour", 60),
    ("In 2 hours", 120),
    ("In 4 hours", 240),
    ("In 6 hours", 360),
    ("In 8 hours", 480),
]


def _format_time(start_time: datetime) -> str:
    return f"{discord.utils.format_dt(start_time, style='F')} ({discord.utils.format_dt(start_time, style='R')})"


def build_vote_embed(guild: discord.Guild, start_time: datetime, vote_count: int) -> discord.Embed:
    state = get_custom_stn(guild.id)
    creator_id = int(state["created_by"]) if state else 0
    channel_id = int(state["channel_id"]) if state else 0
    channel = guild.get_channel(channel_id) if channel_id else None
    channel_name = getattr(channel, "mention", None) or getattr(channel, "name", "this channel")

    embed = discord.Embed(
        title="🛠️ Custom STN Vote",
        description=(
            f"Vote yes to launch the custom in {channel_name}.\n"
            f"The event will be created automatically at **{YES_THRESHOLD}** yes vote(s)."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Start Time", value=_format_time(start_time), inline=False)
    embed.add_field(name="Yes Votes", value=f"{vote_count}/{YES_THRESHOLD}", inline=True)
    embed.add_field(name="Created By", value=f"<@{creator_id}>" if creator_id else "Unknown", inline=True)
    embed.set_footer(text="Use the button below to vote. One yes vote per user.")
    return embed


def build_created_embed(guild: discord.Guild, event: discord.ScheduledEvent) -> discord.Embed:
    embed = discord.Embed(
        title="✅ Custom Event Created",
        description=f"The scheduled event is live: [{event.name}]({event.url})",
        color=discord.Color.green(),
    )
    embed.add_field(name="Starts", value=_format_time(event.start_time), inline=False)
    if event.end_time:
        embed.add_field(name="Ends", value=_format_time(event.end_time), inline=False)
    if event.location:
        embed.add_field(name="Location", value=event.location, inline=False)

    embed.set_footer(text=f"Created in {guild.name}")
    return embed


class CustomSTNTimeSelect(discord.ui.Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label=label, value=str(minutes))
            for label, minutes in TIME_PRESETS
        ]
        super().__init__(placeholder="Choose the custom start time", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, CustomSTNTimeSelectView):
            return

        minutes = int(self.values[0])
        start_time = discord.utils.utcnow() + timedelta(minutes=minutes)
        await view.publish_vote(interaction, start_time)


class CustomSTNTimeSelectView(discord.ui.View):
    def __init__(self, publish_vote: Callable[[discord.Interaction, datetime], Awaitable[None]]) -> None:
        super().__init__(timeout=120)
        self.publish_vote_callback = publish_vote
        self.add_item(CustomSTNTimeSelect())

    async def publish_vote(self, interaction: discord.Interaction, start_time: datetime) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.publish_vote_callback(interaction, start_time)
        except Exception as exc:  # pragma: no cover - defensive message for admins
            await interaction.edit_original_response(content=f"Could not start the vote: {type(exc).__name__}: {exc}")
            return

        await interaction.edit_original_response(content=f"Posted the vote for {discord.utils.format_dt(start_time, style='R')}.")
        self.stop()


class CustomSTNVoteView(discord.ui.View):
    def __init__(self, guild_id: int, start_time: datetime, creator_id: int) -> None:
        super().__init__(timeout=86400)
        self.guild_id = int(guild_id)
        self.start_time = start_time
        self.creator_id = int(creator_id)

    def _current_vote_count(self) -> int:
        state = get_custom_stn(self.guild_id)
        if not state:
            return 0
        return len(state["yes_voters"])

    async def _refresh_vote_message(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            return
        embed = build_vote_embed(interaction.guild, self.start_time, self._current_vote_count())
        await interaction.message.edit(embed=embed, view=self)

    async def _disable_buttons(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True

    async def _create_custom_event(self, interaction: discord.Interaction) -> discord.ScheduledEvent:
        guild = interaction.guild
        if guild is None:
            raise RuntimeError("This command can only be used in a server.")

        message_channel = interaction.message.channel
        description = (
            f"Created from a custom vote in #{getattr(message_channel, 'name', 'customs')}.",
        )

        end_time = self.start_time + timedelta(hours=2)

        if isinstance(message_channel, (discord.VoiceChannel, discord.StageChannel)):
            return await guild.create_scheduled_event(
                name="Custom STN",
                start_time=self.start_time,
                end_time=end_time,
                privacy_level=discord.PrivacyLevel.guild_only,
                channel=message_channel,
                description=description[0],
                reason="Custom STN vote reached the approval threshold.",
            )

        location = getattr(message_channel, "name", None) or guild.name
        return await guild.create_scheduled_event(
            name="Custom STN",
            start_time=self.start_time,
            end_time=end_time,
            entity_type=discord.EntityType.external,
            privacy_level=discord.PrivacyLevel.guild_only,
            location=location,
            description=description[0],
            reason="Custom STN vote reached the approval threshold.",
        )

    @discord.ui.button(label=f"Yes (0/{YES_THRESHOLD})", style=discord.ButtonStyle.success)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("Use this in a server.", ephemeral=True)
            return

        state = get_custom_stn(self.guild_id)
        if not state:
            await interaction.response.send_message("No active custom vote is running.", ephemeral=True)
            return

        if state.get("message_id") and int(state["message_id"]) != int(interaction.message.id):
            await interaction.response.send_message("This vote is no longer active.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        ok, message, vote_count = cast_yes_vote(self.guild_id, interaction.message.id, interaction.user.id)
        if not ok:
            await interaction.followup.send(message, ephemeral=True)
            return

        button.label = f"Yes ({vote_count}/{YES_THRESHOLD})"

        if vote_count < YES_THRESHOLD:
            await self._refresh_vote_message(interaction)
            await interaction.followup.send(f"Vote counted. {vote_count}/{YES_THRESHOLD} yes.", ephemeral=True)
            return

        if not reserve_event_creation(self.guild_id):
            await interaction.followup.send("The scheduled event is already being created.", ephemeral=True)
            return

        try:
            event = await self._create_custom_event(interaction)
        except (discord.Forbidden, discord.HTTPException) as exc:
            abort_event_creation(self.guild_id)
            await self._refresh_vote_message(interaction)
            await interaction.followup.send(
                f"I couldn't create the scheduled event: {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return

        finish_event_creation(self.guild_id, event.id)
        await self._disable_buttons()
        clear_custom_stn(self.guild_id)

        created_embed = build_created_embed(interaction.guild, event)
        await interaction.message.edit(embed=created_embed, view=self)
        await interaction.followup.send(f"Custom event created: {event.url}")
        self.stop()


def build_time_select_view(publish_vote: Callable[[discord.Interaction, datetime], Awaitable[None]]) -> CustomSTNTimeSelectView:
    return CustomSTNTimeSelectView(publish_vote)


def build_vote_view(guild_id: int, start_time: datetime, creator_id: int) -> CustomSTNVoteView:
    return CustomSTNVoteView(guild_id, start_time, creator_id)
