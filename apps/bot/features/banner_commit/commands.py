import io

import discord
from discord.ext import commands


TRIGGER_KEY = "RIFT_BANNER_COMMIT__Q7xN2vLm9TpR4kZ8"
TARGET_CHANNEL_ID = 1499895924720275586


class BannerCommit(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Listen for banner commit trigger and update server banner."""
        # Ignore DMs
        if message.guild is None:
            return

        # Check if message is in the target channel
        if message.channel.id != TARGET_CHANNEL_ID:
            return

        # Check if message contains only the trigger key
        if message.content.strip() != TRIGGER_KEY:
            return

        # Check if author is a bot or webhook
        if not (message.author.bot or isinstance(message.author, discord.WebhookUser)):
            print(f"[Banner Commit] Rejected: Author is not a bot or webhook ({message.author})")
            return

        # Verify bot has Manage Guild permission
        if not message.guild.me.guild_permissions.manage_guild:
            error_msg = "[Banner Commit] ❌ Error: Bot lacks MANAGE_GUILD permission"
            print(error_msg)
            await message.channel.send(error_msg)
            return

        try:
            # Look backward for the most recent message with an image attachment
            image_message = None
            async for prev_message in message.channel.history(
                limit=100, before=message
            ):
                if prev_message.attachments:
                    for attachment in prev_message.attachments:
                        if attachment.content_type and attachment.content_type.startswith("image/"):
                            image_message = prev_message
                            attachment_to_use = attachment
                            break
                    if image_message:
                        break

            if not image_message or not attachment_to_use:
                error_msg = "[Banner Commit] ❌ Error: No image attachment found in recent messages"
                print(error_msg)
                await message.channel.send(error_msg)
                return

            # Download the image bytes
            image_bytes = await attachment_to_use.read()

            # Update the server banner
            await message.guild.edit(banner=image_bytes)
            print(f"[Banner Commit] ✅ Successfully set server banner from {image_message.author} ({image_message.id})")

        except discord.Forbidden:
            error_msg = "[Banner Commit] ❌ Error: Bot lacks permission to manage guild"
            print(error_msg)
            await message.channel.send(error_msg)
        except Exception as e:
            error_msg = f"[Banner Commit] ❌ Error: {type(e).__name__}: {str(e)}"
            print(error_msg)
            await message.channel.send(error_msg)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BannerCommit(bot))
