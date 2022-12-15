import asyncio
import os

import discord
import requests
from discord import Embed
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def help(self, ctx: commands.context.Context):
        """Return a help command"""

        await ctx.send("This is a help command.")

    @commands.command()
    async def UwU(self, ctx: commands.context.Context):
        """Return the gesture"""

        await ctx.send("UwU")

    @commands.command()
    async def avatar(self, ctx: commands.context.Context, user: str):
        """Send back the mentioned users avatar"""

        user_obj: discord.member.Member = await self.parse_user(ctx, user)
        if user_obj is None:
            await ctx.channel.send("User could not be found!")
            return

        # Download the user's avatar
        response = requests.get(user_obj.avatar.url)
        if response.status_code == 200:
            with open(f"avatars/{user_obj}.png", "wb") as f:
                f.write(response.content)
            avatar_file = discord.File(f"avatars/{user_obj}.png", filename=f"{user_obj}.png")
            await ctx.channel.send(f"Profile picture of {user_obj}:", file=avatar_file)
            os.remove(f"avatars/{user_obj}.png")
        else:
            await ctx.channel.send("Failed to download avatar.")

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

    await bot.add_cog(General(bot))
