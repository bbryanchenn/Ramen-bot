from discord import Interaction, app_commands
from discord.ext import commands


DEFAULT_SETTINGS = {
    "teams": 2,
    "strict_roles": True,
    "default_mmr": 500,
    "role_map": {
        "TOP": "Top",
        "JUNGLE": "Jungle",
        "MID": "Mid",
        "ADC": "ADC",
        "SUPPORT": "Support",
        "FILL": "Fill",
    },
}


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.guild_settings: dict[int, dict] = {}

    def get_settings(self, guild_id: int) -> dict:
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = DEFAULT_SETTINGS.copy()
        return self.guild_settings[guild_id]

    # ------------------------
    # VIEW SETTINGS
    # ------------------------
    @app_commands.command(name="settings", description="View current settings")
    async def settings(self, interaction: Interaction) -> None:
        cfg = self.get_settings(interaction.guild.id)

        msg = (
            f"**Teams:** {cfg['teams']}\n"
            f"**Strict Roles:** {cfg['strict_roles']}\n"
            f"**Default MMR:** {cfg['default_mmr']}\n"
            f"**Role Map:**\n"
        )

        for k, v in cfg["role_map"].items():
            msg += f"{k} → {v}\n"

        await interaction.response.send_message(msg)

    # ------------------------
    # SET TEAM COUNT
    # ------------------------
    @app_commands.command(name="setteams", description="Set number of teams (2 or 3)")
    async def setteams(self, interaction: Interaction, count: int) -> None:
        if count not in (2, 3):
            await interaction.response.send_message("Only 2 or 3 teams supported", ephemeral=True)
            return

        cfg = self.get_settings(interaction.guild.id)
        cfg["teams"] = count

        await interaction.response.send_message(f"Teams set to {count}")

    # ------------------------
    # TOGGLE STRICT ROLES
    # ------------------------
    @app_commands.command(name="strictroles", description="Toggle strict role mode")
    async def strictroles(self, interaction: Interaction) -> None:
        cfg = self.get_settings(interaction.guild.id)
        cfg["strict_roles"] = not cfg["strict_roles"]

        await interaction.response.send_message(
            f"Strict roles: {cfg['strict_roles']}"
        )

    # ------------------------
    # SET DEFAULT MMR
    # ------------------------
    @app_commands.command(name="defaultmmr", description="Set fallback MMR")
    async def defaultmmr(self, interaction: Interaction, mmr: int) -> None:
        cfg = self.get_settings(interaction.guild.id)
        cfg["default_mmr"] = mmr

        await interaction.response.send_message(f"Default MMR set to {mmr}")

    # ------------------------
    # SET ROLE NAME
    # ------------------------
    @app_commands.command(name="setrole", description="Map a lane to a Discord role name")
    async def setrole(self, interaction: Interaction, lane: str, role_name: str) -> None:
        lane = lane.upper()

        if lane not in ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT", "FILL"]:
            await interaction.response.send_message("Invalid lane", ephemeral=True)
            return

        cfg = self.get_settings(interaction.guild.id)
        cfg["role_map"][lane] = role_name

        await interaction.response.send_message(f"{lane} mapped to '{role_name}'")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Settings(bot))