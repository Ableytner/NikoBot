"""contains the cog of the dev module"""

from abllib import PersistentStorage, VolatileStorage, CacheStorage, StorageView
from abllib.storage import _PersistentStorage, _VolatileStorage, _CacheStorage, _StorageView
from abllib._storage import _BaseStorage
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
        "testfunc",
        "run the test function for debugging purposes, does nothing in production environment",
        command_group,
        hidden=True
    )
    async def testfunc(self, _: commands.context.Context):
        """run the test function for debugging purposes, does nothing in production environment"""

        return

    @grouped_normal_command(
        "sync_tree",
        "sync the bots tree to load new slash commands",
        command_group,
        hidden=True
    )
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
    async def get(self, ctx: commands.context.Context, storage_name: str, key: str):
        """return a value from the given storage"""

        storage = self._parse_storage(storage_name)
        if storage is None:
            await reply(ctx, f"unknown storage type '{storage_name}'")
            return

        if key not in storage:
            await reply(ctx, f"key '{key}' is not in {storage.name}")
            return

        await reply(ctx, str(storage[key]))

    @grouped_normal_command(
        "set",
        "set a key from the given storage to a given value",
        command_group,
        hidden=True
    )
    async def set(self, ctx: commands.context.Context, storage_name: str, key: str, value: str):
        """set a key from the given storage to a given value"""

        storage = self._parse_storage(storage_name)
        if storage is None:
            await reply(ctx, f"unknown storage type '{storage_name}'")
            return

        storage[key] = value
        await reply(ctx, "success")

    @grouped_normal_command(
        "pop",
        "remove and return a key from the requested storage object",
        command_group,
        hidden=True
    )
    async def pop(self, ctx: commands.context.Context, storage_name: str, key: str | None):
        """remove and return a key from the requested storage object"""

        storage = self._parse_storage(storage_name)
        if storage is None:
            await reply(ctx, f"unknown storage type '{storage_name}'")
            return

        if isinstance(storage, _StorageView):
            await reply(ctx, "StorageView is read-only'")
            return

        if key not in storage:
            await reply(ctx, f"key '{key}' is not in {storage.name}")
            return

        await reply(ctx, str(storage.pop(key)))

    @grouped_normal_command(
        "keys",
        "return all keys from the requested storage object, or all keys if the given key is omitted",
        command_group,
        hidden=True
    )
    async def keys(self, ctx: commands.context.Context, storage_name: str, key: str | None):
        """return all keys from the requested storage object, or all keys if the given key is omitted"""

        storage = self._parse_storage(storage_name)
        if storage is None:
            await reply(ctx, f"unknown storage type '{storage_name}'")
            return

        if key is None:
            storage_obj = storage
        else:
            if key not in storage:
                await reply(ctx, f"key '{key}' is not in {storage.name}")
                return

            storage_obj = storage[key]

        if not isinstance(storage_obj, (dict, _BaseStorage, _StorageView)):
            await reply(ctx, f"Requested object is not of type '{dict}', but '{type(storage_obj)}'")
            return

        # cast to list for more beautiful print
        keys = list(storage_obj.keys())
        await reply(ctx, str(keys))

    def _parse_storage(self, storage_name: str) \
       -> _StorageView | _PersistentStorage | _VolatileStorage | _CacheStorage | None:
        storage_name = storage_name.lower().strip()

        if storage_name in "storageview":
            return StorageView
        if storage_name in "persistentstorage":
            return PersistentStorage
        if storage_name in "volatilestorage":
            return VolatileStorage
        if storage_name in "cachestorage":
            return CacheStorage

        return None

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Dev(bot))
