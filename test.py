import asyncio

import discord
from discord import Embed
from discord.ext import commands

class Test(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.data = 0

    @commands.command()
    async def add(self, ctx: commands.context.Context):
        """Return a help command"""

        self.data += 1
    
    @commands.command()
    async def get(self, ctx: commands.context.Context):
        await ctx.channel.send(str(self.data))

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Test(bot))
