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

        repo_base = None
        for repo in VolatileStorage["oslinker.repos"]:
            if repo["channel_id"] == message.channel.id:
                repo_base = repo["repo_base"]
                break

        if repo_base is None:
            return

        content = message.content

        replies = []

        pr_matches = re.findall(r"!\d{1,4}", content)
        if len(pr_matches) != 0 \
           and re.search(r"\[!\d{1,4}\]", content) is None:
            for pr_id in set(pr_matches):
                url = f"{repo_base}/-/merge_requests/{pr_id.strip('!')}"
                replies.append(f"Linked PR: [{pr_id}]({url})")

        issue_matches = re.findall(r"#\d{1,4}", content)
        if len(issue_matches) != 0 \
           and re.search(r"\[#\d{1,4}\]", content) is None:
            for issue_id in set(issue_matches):
                url = f"{repo_base}/-/work_items/{issue_id.strip('#')}"
                replies.append(f"Linked Issue: [{issue_id}]({url})")

        if len(replies) > 0:
            await discord.channel_message(message.channel.id, "\n".join(replies))

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    config = util.general.load_config()

    if "oslinker" not in config \
       or "repos" not in config["oslinker"] \
       or not isinstance(config["oslinker"]["repos"], list) \
       or len(config["oslinker"]["repos"]) == 0:
        raise ValueError("Missing repos for use with the oslinker module.")

    repos = []
    for entry in config["oslinker"]["repos"]:
        if "repo_base" not in entry or entry["repo_base"] == "":
            raise ValueError("Missing repo_base for use with the oslinker module.")
        if "channel_id" not in entry or entry["channel_id"] == "":
            raise ValueError("Missing channel_id for use with the oslinker module.")
        repos.append({"repo_base": entry["repo_base"], "channel_id": int(entry["channel_id"])})

    VolatileStorage["oslinker.repos"] = repos

    await bot.add_cog(OSLinker(bot))
