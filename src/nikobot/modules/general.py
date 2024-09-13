"""A module containing general commands"""

from discord.ext import commands

class General(commands.Cog):
    """A ``discord.commands.Cog`` containing general commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(brief="Return the gesture", description="Return the gesture.")
    async def UwU(self, ctx: commands.context.Context):
        """
        Return the gesture
        
        This is the most basic command that should work no matter what
        """

        await ctx.send("UwU")

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(General(bot))
