from pathlib import Path

import discord
from discord.ext import commands

from apps.bot.utils.env import get_env


class LeagueBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.message_content = False

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

        self.guild_id = int(get_env("DISCORD_GUILD_ID", "0") or "0")
        self.initial_extensions = self._discover_extensions()

    def _discover_extensions(self) -> list[str]:
        base_dir = Path(__file__).parent

        command_extensions = [
            f"apps.bot.commands.{path.stem}"
            for path in sorted((base_dir / "commands").glob("*.py"))
            if not path.stem.startswith("__")
        ]

        feature_extensions = [
            f"apps.bot.features.{path.name}.commands"
            for path in sorted((base_dir / "features").iterdir())
            if path.is_dir()
            and not path.name.startswith("__")
            and (path / "commands.py").exists()
        ]

        return command_extensions + feature_extensions

    async def setup_hook(self) -> None:
        for ext in self.initial_extensions:
            await self.load_extension(ext)

        if self.guild_id:
            guild = discord.Object(id=self.guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self) -> None:
        if self.user is not None:
            print(f"Logged in as {self.user} ({self.user.id})")
        activity = discord.Activity(
            type=discord.ActivityType.competing,
            name="balanced 5v5s"
            )
        await self.change_presence(status=discord.Status.online, activity=activity)