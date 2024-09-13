"""A module containing the clear command"""

import discord
from discord.ext import commands

from .. import util

class Clear(commands.Cog):
    """A ``discord.commands.Cog`` containing the clear command"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self._to_clear = {}
        self._yes_emoji = "✅"
        self._no_emoji = "❌"

    @util.discord.hybrid_command(
        "clear",
        "Delete the given amount of messages"
    )
    async def clear(self, ctx: commands.context.Context | discord.interactions.Interaction, amount: int):
        """Discord command that deletes the given amount of messages,
        as well as the message containing the initial command"""

        accept_decline = await util.discord.reply(ctx, f"Are you sure you want to delete {amount} messages?")
        await accept_decline.add_reaction(self._yes_emoji)
        await accept_decline.add_reaction(self._no_emoji)

        amount += 1 if util.discord.is_slash_command(ctx) else 2

        self._to_clear[accept_decline.id] = {
            "channel_id": ctx.channel.id,
            "message_id": accept_decline.id,
            "amount": amount
        }

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.reaction.Reaction, user: discord.member.Member):
        """Discord listener that is called when a reaction is added to any message"""

        if user.id == util.discord.get_bot().user.id:
            return
        if reaction.message.id not in self._to_clear:
            return

        data = self._to_clear[reaction.message.id]

        if reaction.emoji == "✅":
            await self.bot.get_channel(data["channel_id"]).purge(limit=data["amount"])
            self._to_clear.pop(reaction.message.id)
        elif reaction.emoji == "❌":
            await self.bot.get_channel(data["channel_id"]).get_partial_message(data["message_id"]).clear_reactions()
            self._to_clear.pop(reaction.message.id)
        else:
            return

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Clear(bot))
