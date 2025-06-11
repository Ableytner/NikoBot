"""contains the cog of the dev module"""

from abllib import PersistentStorage, VolatileStorage, CacheStorage
from abllib.storage import _PersistentStorage, _VolatileStorage, _CacheStorage
from abllib.log import get_logger
from discord import app_commands
from discord.ext import commands

from ..util.discord import grouped_normal_command, reply

# pylint: disable=broad-exception-caught

logger = get_logger("dev")

command_group = app_commands.Group(
    name="dev",
    description="The module for development-related commands"
)

class Dev(commands.Cog):
    """The module for development-related commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @grouped_normal_command(
        "sync_tree",
        "sync the bots tree to load new slash commands",
        command_group,
        hidden=True
    )
    @commands.is_owner()
    async def sync_tree(self, ctx: commands.context.Context):
        """sync the bots tree to load new slash command"""

        msg = await ctx.reply("syncing tree...")
        await self.bot.tree.sync()
        await msg.edit(content="done syncing tree")

    @grouped_normal_command(
        "get",
        "return a value from the given storage",
        command_group,
        hidden=True
    )
    @commands.is_owner()
    async def get(self, ctx: commands.context.Context, storage_name: str, key: str):
        """return a value from the given storage"""

        storage = self._parse_storage(storage_name)

        try:
            await reply(ctx, str(storage[key]))
        except Exception as e:
            await reply(ctx, f"Error occured:\n{str(e)}")

    @grouped_normal_command(
        "set",
        "set a key from the given storage to a given value",
        command_group,
        hidden=True
    )
    @commands.is_owner()
    async def set(self, ctx: commands.context.Context, storage_name: str, key: str, value: str):
        """set a key from the given storage to a given value"""

        storage = self._parse_storage(storage_name)

        try:
            storage[key] = value
            await reply(ctx, "success")
        except Exception as e:
            await reply(ctx, f"Error occured:\n{str(e)}")

    @grouped_normal_command(
        "keys",
        "return all keys from the given storage object",
        command_group,
        hidden=True
    )
    @commands.is_owner()
    async def keys(self, ctx: commands.context.Context, storage_name: str, key: str):
        """return all keys from the given storage object"""

        storage = self._parse_storage(storage_name)

        try:
            if not isinstance(storage[key], dict):
                await reply(ctx, f"Requested object is not of type {dict}, but {type(storage[key])}")
                return

            # cast to list for more beautiful print
            keys = list(storage[key].keys())
            await reply(ctx, str(keys))
        except Exception as e:
            await reply(ctx, f"Error occured:\n{str(e)}")

    def _parse_storage(self, storage_name: str) -> _PersistentStorage | _VolatileStorage | _CacheStorage:
        storage_name = storage_name.lower().strip()

        if storage_name in "persistentstorage":
            return PersistentStorage
        if storage_name in "volatilestorage":
            return VolatileStorage
        if storage_name in "cachestorage":
            return CacheStorage

        raise ValueError(f"Expected valid storage name, not '{storage_name}'")

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Dev(bot))
