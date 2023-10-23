from discord import Embed
from discord.ext import commands

class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(name="help", brief="Return a help command", description="Show information about a command or module.", with_app_command=True)
    async def help(self, ctx: commands.context.Context, command_name: str = None):
        if command_name is None:
            cmds: list[tuple[str, str]] = []
            for cmd in self.bot.commands:
                cmds.append((cmd.name, cmd.brief))

            answer = Embed(title="All available commands")
            for name, desc in cmds:
                answer.add_field(name=name, value=desc, inline=False)
        else:
            cmds: list[tuple[str, str]] = []
            for cmd in self.bot.commands:
                cmds.append((cmd.name, cmd.description))
            for cog_name, cog in self.bot.cogs.items():
                cmds.append((cog_name, cog.description))

            for name, desc in cmds:
                if name.lower() == command_name.lower():
                    answer = Embed(title=f"Help for '{name}'")
                    answer.add_field(name="Description", value=desc)

        await ctx.reply(embed=answer)

    @commands.command(brief="Return the gesture", description="Return the gesture.")
    async def UwU(self, ctx: commands.context.Context):
        await ctx.send("UwU")

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(General(bot))
