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

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(General(bot))
