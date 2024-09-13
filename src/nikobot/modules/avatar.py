"""A module containing the avatar command"""

import os

import discord
import requests
from discord.ext import commands

from .. import util

class Avatar(commands.Cog):
    """A ``discord.commands.Cog`` containing the avatar command"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @util.discord.hybrid_command(
        "avatar",
        "Send back the mentioned users avatar"
    )
    async def avatar(self, ctx: commands.context.Context | discord.interactions.Interaction, *user: list[str]):
        """Send back the mentioned users avatar"""

        recombined_user = " ".join(["".join(item) for item in user])

        user_obj: discord.member.Member | None = await util.discord.parse_user(ctx, recombined_user)
        if user_obj is None:
            await util.discord.reply(ctx, "User could not be found!")
            return
        if user_obj.avatar is None:
            await util.discord.reply(ctx, "User has a default avatar, which can't be downloadad.")
            return

        os.makedirs(f"{util.VolatileStorage["cache_dir"]}/avatars", exist_ok=True)

        # Download the user's avatar
        response = requests.get(user_obj.avatar.url, timeout=30)
        if response.status_code == 200:
            with open(f"{util.VolatileStorage["cache_dir"]}/avatars/{user_obj}.png", "wb") as f:
                f.write(response.content)
        else:
            await util.discord.reply(ctx, "Failed to download avatar.")

        # send the avatar
        avatar_file = discord.File(f"{util.VolatileStorage["cache_dir"]}/avatars/{user_obj}.png",
                                   filename=f"{user_obj}.png")
        await util.discord.reply(ctx,
                                 f"Profile picture of {user_obj.nick or user_obj.display_name or user_obj.name}:",
                                 file=avatar_file)

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Avatar(bot))
