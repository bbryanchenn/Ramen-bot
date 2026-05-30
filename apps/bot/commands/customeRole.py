import discord
from discord.ext import commands
from discord import app_commands

ROLE_ID = 1486158206492475484

class RoleIDs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roleids", description="Get all user IDs with a specific role")
    @app_commands.checks.has_permissions(administrator=True)
    async def roleids(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(ROLE_ID)

        if not role:
            await interaction.response.send_message("Role not found.", ephemeral=True)
            return

        ids = sorted(role.members, key=lambda m: m.display_name.lower())

        if not ids:
            await interaction.response.send_message("No members found with that role.", ephemeral=True)
            return

        output = "users = [\n"
        output += ",\n".join(
            f"    {member.id},  # {member.display_name} ({member.name})"
            for member in ids
        )
        output += "\n]"

        if len(output) > 1900:
            with open("role_ids.txt", "w") as f:
                f.write(output)

            await interaction.response.send_message(
                file=discord.File("role_ids.txt"),
                ephemeral=False
            )
        else:
            await interaction.response.send_message(
                f"```py\n{output}\n```",
                ephemeral=False
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(RoleIDs(bot))