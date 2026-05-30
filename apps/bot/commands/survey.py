import discord
from discord.ext import commands
from discord import app_commands

users = [
    708517923240542251,  # Angel⭐ (angelstarchild),
    384067083497111563,  # Blendi (a1adeen),
    692837353340928052,  # Eman (emanr1209),
    361678318874918924,  # Filthyphil (_filthyphil),
    180793199349071872,  # Harleybou (harleybou),
    867754044843098143,  # Ken (winnek),
    471199925938552833,  # Me17Today (me17today),
    296047079896121345,  # Orpid (orpie),
    584197648769089536,  # pav (alienkid993),
    1409168592485879839, # porcel (.porcel.),
    425669291539562527,  # Psionic (psionic216),
    253802992271097856,  # RoyalKamper (kamper275),
    719617559539875971,  # Royce (woycie),
    80923523949793280,   # Rush (denis.s),
]

testingDebug = False
ADMIN_ID = 444188728500551690
TEST_CHANNEL_ID = 1494753475236724776
SURVEY_LINK = "https://forms.gle/QFLEH4Yik1dCNnjy9"


class SurveyView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(
        label="Open Survey",
        style=discord.ButtonStyle.green,
        custom_id="survey_open"
    )
    async def open_survey(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            f"Here’s the survey:\n{SURVEY_LINK}",
            ephemeral=True
        )

        try:
            admin = await self.bot.fetch_user(ADMIN_ID)
            await admin.send(f"{interaction.user} clicked the survey button.")
        except Exception as e:
            print(f"Could not DM admin: {e}")


class Survey(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="survey", description="Send the survey embed")
    async def survey(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Quick Server Survey",
            description=(
                "Hey you! We’re trying to get everyone’s input for the in-house tournament.\n\n"
                "The survey was posted in the <#1463804527173046375>, but a lot of people probably missed it, "
                "so I’m sending it here privately to you.\n\n"
                "**Please fill it out when you get a chance, or else...**\n"
            ),
            color=discord.Color.red()
        )

        embed.set_footer(
            text="From the desk of the visionary, LYFESTYLE"
        )

        view = SurveyView(self.bot)

        if testingDebug:
            channel = self.bot.get_channel(TEST_CHANNEL_ID)
            await channel.send(embed=embed, view=view)
            await interaction.response.send_message("Survey sent to test channel.", ephemeral=True)
        else:
            sent = 0

            for user_id in users:
                try:
                    user = await self.bot.fetch_user(user_id)
                    await user.send(embed=embed, view=view)
                    sent += 1
                except Exception as e:
                    print(f"Could not send DM to {user_id}: {e}")

            await interaction.response.send_message(
                f"Survey sent to {sent} users.",
                ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Survey(bot))