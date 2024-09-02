import os

import discord
import requests
from discord.ext import commands

class Avatar(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        if not os.path.exists(os.path.join("cache", "avatars")):
            os.mkdir(os.path.join("cache", "avatars"))

    @commands.command()
    async def avatar(self, ctx: commands.context.Context, user: str):
        """Send back the mentioned users avatar"""

        user_obj: discord.member.Member | None = await self.parse_user(ctx, user)
        if user_obj is None:
            await ctx.message.reply("User could not be found!")
            return
        if user_obj.avatar is None:
            await ctx.message.reply("User has a default avatar, which can't be downloadad.")
            return
        
        # Download the user's avatar
        response = requests.get(user_obj.avatar.url)
        if response.status_code == 200:
            with open(f"cache/avatars/{user_obj}.png", "wb") as f:
                f.write(response.content)
        else:
            await ctx.message.reply("Failed to download avatar.")

        # send the avatar
        avatar_file = discord.File(f"cache/avatars/{user_obj}.png", filename=f"{user_obj}.png")
        await ctx.message.reply(f"Profile picture of {user_obj.nick or user_obj.display_name or user_obj.name}:", file=avatar_file)

    async def parse_user(self, ctx: commands.context.Context, user: any) -> discord.member.Member | None:
        if user == None:
            return None

        if isinstance(user, str):
            user = user.strip('"')

        try:
            converter = commands.MemberConverter()
            user = await converter.convert(ctx, user) # convert string to user
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
