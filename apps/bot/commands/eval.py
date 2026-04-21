import asyncio
import inspect
import re
import textwrap
import traceback

import discord
from discord import Interaction, app_commands
from discord.ext import commands


ALLOWED_USER_ID = 444188728500551690


class Eval(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def _normalize_source(code: str) -> str:
        source = code.strip()

        # Unwrap markdown code blocks like ```py ... ```.
        if source.startswith("```") and source.endswith("```"):
            source = re.sub(r"^```(?:python|py)?\s*", "", source, count=1, flags=re.IGNORECASE)
            source = source[:-3].strip()

        # Handle escaped newlines from slash command inputs.
        source = source.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")
        return textwrap.dedent(source).strip()

    @app_commands.command(name="eval", description="Run arbitrary Python code")
    async def eval(self, interaction: Interaction, code: str) -> None:
        if interaction.user.id != ALLOWED_USER_ID:
            await interaction.response.send_message(
                "You are not authorized to use this command.",
                ephemeral=True,
            )
            return

        lobby_cog = self.bot.get_cog("Lobby")
        env = {
            "bot": self.bot,
            "interaction": interaction,
            "discord": discord,
            "commands": commands,
            "asyncio": asyncio,
            "inspect": inspect,
            "get_players": (lambda: getattr(lobby_cog, "players", {})),
        }
        env.update(globals())
        source = self._normalize_source(code)

        if not source:
            await interaction.response.send_message(
                "No code provided.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            result = None
            source_variants = [source]
            if "\n" not in source and "  " in source:
                source_variants.append(re.sub(r"\s{2,}", "; ", source))

            last_exception: Exception | None = None
            for candidate in source_variants:
                try:
                    try:
                        compiled = compile(candidate, "<eval>", "eval")
                        result = eval(compiled, env)
                        if inspect.isawaitable(result):
                            result = await result
                    except SyntaxError:
                        exec(
                            f"async def __eval_function():\n{textwrap.indent(candidate, '    ')}",
                            env,
                        )
                        result = await env["__eval_function"]()
                    last_exception = None
                    break
                except Exception as exc:
                    last_exception = exc

            if last_exception is not None:
                raise last_exception

            if result is not None:
                output = str(result)
            else:
                output = "Executed successfully (no return value)."

            if len(output) > 1900:
                output = output[:1900] + "\n... (truncated)"

            await interaction.followup.send(f"```py\n{output}\n```", ephemeral=True)
        except Exception:
            error = traceback.format_exc()
            if len(error) > 1900:
                error = error[:1900] + "\n... (truncated)"
            await interaction.followup.send(f"```py\n{error}\n```", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Eval(bot))
