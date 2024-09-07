import os

import discord
import requests
from discord.ext import commands

from .. import util

class Avatar(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        if not os.path.exists(os.path.join("cache", "avatars")):
            os.mkdir(os.path.join("cache", "avatars"))

    @util.discord.hybrid_command(
        "avatar",
        "Send back the mentioned users avatar"
    )
    async def avatar(self, ctx: commands.context.Context | discord.interactions.Interaction, user: str):
        """Send back the mentioned users avatar"""

        user_obj: discord.member.Member | None = await self.parse_user(ctx, user)
        if user_obj is None:
            await util.discord.reply(ctx, "User could not be found!")
            return
        if user_obj.avatar is None:
            await util.discord.reply(ctx, "User has a default avatar, which can't be downloadad.")
            return

        # Download the user's avatar
        response = requests.get(user_obj.avatar.url)
        if response.status_code == 200:
            with open(f"cache/avatars/{user_obj}.png", "wb") as f:
                f.write(response.content)
        else:
            await util.discord.reply(ctx, "Failed to download avatar.")

        # send the avatar
        avatar_file = discord.File(f"cache/avatars/{user_obj}.png", filename=f"{user_obj}.png")
        await util.discord.reply(ctx, f"Profile picture of {user_obj.nick or user_obj.display_name or user_obj.name}:", file=avatar_file)

    async def parse_user(self, ctx: commands.context.Context | discord.interactions.Interaction, user: str) -> discord.member.Member | None:
        if user == None:
            return None

        if isinstance(user, str):
            user = user.strip('"')

        try:
            # convert string to user
            converter = commands.MemberConverter()
            if not util.discord.is_slash_command(ctx):
                user = await converter.convert(ctx, user)
            else:
                # this is stupid, but it works
                class ConverterCtx():
                    def __init__(slf, bot, message) -> None:
                        slf.bot = bot
                        slf.guild = None
                        slf.message = message

                user = await converter.convert(ConverterCtx(self.bot, ctx.message), user)
            return user
        except:
            pass

        try:
            user: discord.user.User = self.bot.get_user(int(user))
            return user
        except:
            pass
        
        return None

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Avatar(bot))
