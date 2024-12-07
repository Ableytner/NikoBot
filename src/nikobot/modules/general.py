"""A module containing general commands"""

from discord.ext import commands

from nikobot.util import discord

class General(commands.Cog):
    """A ``discord.commands.Cog`` containing general commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(brief="Return the gesture", description="Return the gesture.")
    async def UwU(self, ctx: commands.context.Context):
        """
        Return the gesture
        
        This is the most basic command that should work no matter what.
        It doesn't even use any custom command registration.
        """

        await ctx.send("UwU")

    @discord.normal_command(
        "ping",
        "Send ping to the bot, which responds with pong"
    )
    async def ping(self, ctx: commands.context.Context):
        """Send back pong"""

        await ctx.send("pong")

        self.ctx_hook(ctx)

    def ctx_hook(self, ctx: commands.context.Context):
        """Provide the ctx for tests that overwrite this method"""

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(General(bot))
