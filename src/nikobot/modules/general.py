"""A module containing general commands"""

from discord import Embed
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

    @discord.normal_command("printall", "print all given args in order", hidden=True)
    async def printall(self,
                       ctx: commands.context.Context,
                       arg1: str | None = None,
                       arg2: str | None = None,
                       arg3: str | None = None,
                       arg4: str | None = None,
                       arg5: str | None = None):
        """
        Print all given arguments
        
        This command is used for debugging
        """

        embed = Embed(title="All given arguments:")
        if arg1 is not None:
            embed.add_field(name="arg1", value=arg1)
        if arg2 is not None:
            embed.add_field(name="arg2", value=arg2)
        if arg3 is not None:
            embed.add_field(name="arg3", value=arg3)
        if arg4 is not None:
            embed.add_field(name="arg4", value=arg4)
        if arg5 is not None:
            embed.add_field(name="arg5", value=arg5)
        await discord.reply(ctx, embed=embed)

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
