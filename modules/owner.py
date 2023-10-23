import discord
from discord.ext import commands

class Owner(commands.Cog):
    """The module for owner-only commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name = "sync_tree",
        description = "sync the bots tree to load new slash commands",
        with_app_command = True
    )
    @commands.is_owner()
    async def sync_tree(self, ctx: commands.context.Context):
        """sync the bots tree to load new slash command"""

        msg = await ctx.reply("syncing tree...")
        await self.bot.tree.sync()
        await msg.edit(content="done syncing tree")

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Owner(bot))
