from discord import Embed, Interaction, app_commands
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def _format_commands(commands_list: list[app_commands.Command]) -> list[str]:
        if not commands_list:
            return ["None"]

        chunks: list[str] = []
        current_lines: list[str] = []
        current_len = 0

        for command in commands_list:
            description = command.description or "No description available."
            line = f"/{command.qualified_name} - {description}"

            line_len = len(line) + (1 if current_lines else 0)
            if current_len + line_len > 1024 and current_lines:
                chunks.append("\n".join(current_lines))
                current_lines = [line]
                current_len = len(line)
            else:
                current_lines.append(line)
                current_len += line_len

        if current_lines:
            chunks.append("\n".join(current_lines))

        return chunks

    @app_commands.command(name="help", description="Show all available commands")
    async def help(self, interaction: Interaction) -> None:
        commands_list = [
            command
            for command in self.bot.tree.walk_commands()
            if isinstance(command, app_commands.Command) and command.qualified_name != "help"
        ]
        commands_list.sort(key=lambda command: command.qualified_name)

        feature_commands = [
            command
            for command in commands_list
            if ".features." in (command.module or "")
        ]
        core_commands = [
            command
            for command in commands_list
            if ".features." not in (command.module or "")
        ]

        embed = Embed(
            title="Available Commands",
            description="Here are the slash commands you can use:",
            color=0xE67E22,
        )

        core_chunks = self._format_commands(core_commands)
        for index, chunk in enumerate(core_chunks, start=1):
            name = "Core Commands" if index == 1 else f"Core Commands (cont. {index})"
            embed.add_field(name=name, value=chunk, inline=False)

        feature_chunks = self._format_commands(feature_commands)
        for index, chunk in enumerate(feature_chunks, start=1):
            name = "Feature Commands" if index == 1 else f"Feature Commands (cont. {index})"
            embed.add_field(name=name, value=chunk, inline=False)

        if not commands_list:
            embed.description = "No commands are currently available."

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
