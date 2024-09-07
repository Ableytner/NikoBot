import logging

import discord
from discord.ext import commands

from .. import util

class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(brief="Return the gesture", description="Return the gesture.")
    async def UwU(self, ctx: commands.context.Context):
        await ctx.send("UwU")

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(General(bot))
