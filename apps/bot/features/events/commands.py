import discord
from discord import Interaction, app_commands
from discord.ext import commands

from apps.bot.features.events.service import EVENT_TYPES, clear_event, get_event, random_event_type, set_event


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="event", description="Set the next match event")
    async def event(self, interaction: Interaction, kind: str = "random") -> None:
        kind = kind.upper().strip()

        if kind == "RANDOM":
            kind = random_event_type()

        if kind not in EVENT_TYPES:
            await interaction.response.send_message(
                "Invalid event. Use RANDOM, SALT_SURGE, DOUBLE_DOWN, UNDERDOG, or MVP_BONUS.",
                ephemeral=True,
            )
            return

        set_event(kind)

        embed = discord.Embed(
            title="🎲 Event Activated",
            description=f"Next match event: **{EVENT_TYPES[kind]['label']}**",
            color=discord.Color.purple(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="eventstatus", description="Show the current active event")
    async def eventstatus(self, interaction: Interaction) -> None:
        event = get_event()
        if not event:
            await interaction.response.send_message("No active event.", ephemeral=True)
            return

        event_type = event["type"]
        embed = discord.Embed(
            title="🎲 Active Event",
            description=f"**{EVENT_TYPES[event_type]['label']}**",
            color=discord.Color.purple(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clearevent", description="Clear the current event")
    async def clearevent(self, interaction: Interaction) -> None:
        clear_event()
        await interaction.response.send_message("Event cleared.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Events(bot))