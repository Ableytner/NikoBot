"""A module containing the avatar command"""

import logging
import os
import pathlib

import discord as discordpy
import requests
from discord.ext import commands

from .. import util

logger = logging.getLogger("avatar")

class Avatar(commands.Cog):
    """A ``discord.commands.Cog`` containing the avatar command"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @util.discord.hybrid_command(
        "avatar",
        "Send back the mentioned users avatar"
    )
    async def avatar(self, ctx: commands.context.Context | discordpy.interactions.Interaction, user: str):
        """Send back the mentioned users avatar"""

        logger.debug(f"Searching for avatar of user {user}")

        user_obj: discordpy.member.Member | None = await util.discord.parse_user(ctx, user)
        if user_obj is None:
            await util.discord.reply(ctx, "User could not be found!")
            return
        if user_obj.avatar is None:
            await util.discord.reply(ctx, "User has a default avatar, which can't be downloadad.")
            return

        avatars_dir = str(pathlib.Path(util.VolatileStorage["cache_dir"], "avatars").resolve())
        os.makedirs(avatars_dir, exist_ok=True)
        avatar_dir = str(pathlib.Path(avatars_dir, f"{user_obj}.png").resolve())

        # Download the user's avatar
        response = requests.get(user_obj.avatar.url, timeout=30)
        if response.status_code == 200:
            with open(avatar_dir, "wb") as f:
                f.write(response.content)
        else:
            await util.discord.reply(ctx, "Failed to download avatar.")

        # send the avatar
        avatar_file = discordpy.File(avatar_dir, filename=f"{user_obj}.png")
        await util.discord.reply(ctx,
                                 f"Profile picture of {user_obj.nick or user_obj.display_name or user_obj.name}:",
                                 file=avatar_file)

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Avatar(bot))
