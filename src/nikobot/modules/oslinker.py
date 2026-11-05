"""A module containing the automated OS-linker"""

import re

from abllib import VolatileStorage
import discord as discordpy
from discord.ext import commands

from nikobot.util import discord
from nikobot import util

class OSLinker(commands.Cog):
    """A ``discord.commands.Cog`` which sends the gitlab-teaching link whenever a PR or issue is mentioned"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def on_message(self, message: discordpy.Message):
        """
        Check if the message has an issue or PR and link it
        """

        channel = VolatileStorage["oslinker.channel_id"]

        if message.channel.id != channel:
            return

        content = message.content

        replies = []

        pr_matches = re.findall(r"!\d{1,4}", content)
        if len(pr_matches) != 0 \
           and re.search(r"\[!\d{1,4}\]", content) is None:
            for pr_id in pr_matches:
                url = f"{VolatileStorage['oslinker.repo_base']}/-/merge_requests/{pr_id.strip('!')}"
                replies.append(f"Linked PR: [{pr_id}]({url})")

        issue_matches = re.findall(r"#\d{1,4}", content)
        if len(issue_matches) != 0 \
           and re.search(r"\[#\d{1,4}\]", content) is None:
            for issue_id in issue_matches:
                url = f"{VolatileStorage['oslinker.repo_base']}/-/work_items/{issue_id.strip('#')}"
                replies.append(f"Linked Issue: [{issue_id}]({url})")

        if len(replies) > 0:
            await discord.channel_message(channel, "\n".join(replies))

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    config = util.general.load_config()


    if "oslinker" not in config \
       or "repo_base" not in config["oslinker"] \
       or config["oslinker"]["repo_base"] == "":
        raise ValueError("Missing repo_base for use with the oslinker module.")
    if "oslinker" not in config \
       or "channel_id" not in config["oslinker"] \
       or config["oslinker"]["channel_id"] == "":
        raise ValueError("Missing channel_id for use with the oslinker module.")

    VolatileStorage["oslinker.repo_base"] = config["oslinker"]["repo_base"]
    VolatileStorage["oslinker.channel_id"] = int(config["oslinker"]["channel_id"])

    await bot.add_cog(OSLinker(bot))
