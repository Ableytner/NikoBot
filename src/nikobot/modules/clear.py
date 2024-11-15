"""A module containing the clear command"""

import discord
from discord.ext import commands

from .. import util

class Clear(commands.Cog):
    """A ``discord.commands.Cog`` containing the clear command"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self._yes_emoji = "✅"
        self._no_emoji = "❌"

    @util.discord.hybrid_command(
        "clear",
        "Delete the given amount of messages"
    )
    async def clear(self, ctx: commands.context.Context | discord.interactions.Interaction, amount: int):
        """Discord command that deletes the given amount of messages,
        as well as the message containing the initial command"""

        if util.discord.is_private_channel(ctx):
            await util.discord.reply(ctx, "Cannot delete messages here")
            return

        accept_decline = await util.discord.reply(ctx, f"Are you sure you want to delete {amount} messages?")
        await accept_decline.add_reaction(self._yes_emoji)
        await accept_decline.add_reaction(self._no_emoji)

        amount += 1 if util.discord.is_slash_command(ctx) else 2

        util.PersistentStorage[f"clear.{accept_decline.id}"] = {
            "channel_id": ctx.channel.id,
            "message_id": accept_decline.id,
            "amount": amount,
            "is_slash_command": util.discord.is_slash_command(ctx)
        }

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.reaction.Reaction, user: discord.member.Member):
        """Discord listener that is called when a reaction is added to any message"""

        if user.id == util.discord.get_bot().user.id:
            return
        if str(reaction.message.id) not in util.PersistentStorage["clear"]:
            return
        if reaction.emoji not in [self._yes_emoji, self._no_emoji]:
            return

        data = util.PersistentStorage[f"clear.{reaction.message.id}"]

        channel = util.discord.get_bot().get_channel(data["channel_id"])
        if channel is None:
            raise util.error.NoneTypeException()

        if reaction.emoji == self._yes_emoji:
            await channel.purge(limit=data["amount"])
        else:
            if data["is_slash_command"]:
                await channel.purge(limit=1)
            else:
                await channel.purge(limit=2)

        del util.PersistentStorage[f"clear.{reaction.message.id}"]

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Clear(bot))
