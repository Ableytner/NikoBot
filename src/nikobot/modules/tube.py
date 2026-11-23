"""A module containing the tube commands"""

import os

from abllib.log import get_logger
from discord import app_commands
from discord.ext import commands

from .. import util

logger = get_logger("tube")

TUBE_REQUESTS_FILE = "/tube_requests.txt"

command_group = app_commands.Group(
    name="tube",
    description="The module for Tube-related commands"
)

class Tube(commands.Cog):
    """A ``discord.commands.Cog`` containing the tube commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._file_available = self._check_file()

    def _check_file(self) -> bool:
        """Check that the tube requests file exists and is openable for appending"""

        if not os.path.isfile(TUBE_REQUESTS_FILE):
            logger.error(f"{TUBE_REQUESTS_FILE} does not exist or is not a regular file, "
                         "make sure it is mounted correctly")
            return False

        try:
            with open(TUBE_REQUESTS_FILE, "a", encoding="utf8"):
                pass
        except OSError as e:
            logger.error(f"{TUBE_REQUESTS_FILE} is not openable for appending: {e}")
            return False

        return True

    @util.discord.grouped_normal_command(
        "add",
        "Add a URL or ID to the download queue",
        command_group
    )
    async def add(self, ctx: commands.context.Context, url_or_id: str):
        """Add a URL or ID to the download queue"""

        if not self._file_available:
            await util.discord.reply(ctx, "download queue is not available")
            return

        url_or_id = url_or_id.strip()
        if "\n" in url_or_id or "\r" in url_or_id:
            await util.discord.reply(ctx, "malformed input")
            return

        try:
            with open(TUBE_REQUESTS_FILE, "a", encoding="utf8") as f:
                f.write(url_or_id + "\n")
        except OSError as e:
            logger.error(f"Failed to append to {TUBE_REQUESTS_FILE}: {e}")
            await util.discord.reply(ctx, "failed to add to download queue")
            return

        await util.discord.reply(ctx, "added to download queue")

async def setup(bot: commands.Bot):
    """Setup the tube cog"""

    await bot.add_cog(Tube(bot))
