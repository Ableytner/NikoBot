"""A module containing the ``DiscordBot`` class"""

import pathlib
import shutil
import traceback
import os

import asyncio
import discord
from discord.ext import commands

from nikobot import util

MODULES = ["general", "help", "clear", "music", "avatar", "owner", "tc4.tc4", "mal.malnotifier"]
STORAGE_DIR = str(pathlib.Path(os.path.dirname(__file__), "..", "storage").resolve())
STORAGE_FILE = os.path.join(STORAGE_DIR, "storage.json")
CACHE_DIR = os.path.join(STORAGE_DIR, "cache")
TEMP_DIR = os.path.join(STORAGE_DIR, "temp")

class DiscordBot(commands.Bot):
    """The main ``discord.commands.Bot`` which is the center of the application"""

    def __init__(self) -> None:
        super().__init__(command_prefix = 'niko.', help_command=None, intents = discord.Intents.all())

    def start_bot(self):
        """Start the discord bot"""

        self.run(os.environ["DISCORD_TOKEN"])

    async def setup_hook(self) -> None:
        util.VolatileStorage["modules"] = []
        for module in MODULES:
            await self.load_extension(f"nikobot.modules.{module}")
            util.VolatileStorage["modules"].append(module)
            print(f"Loaded module {module}")

    async def on_ready(self):
        """Method called when the bot is ready"""

        print(f"{self.user} is now online")

    async def on_command_error(self,
                               context: commands.context.Context,
                               exception: commands.errors.CommandError, /) -> None:
        # owner-only commands
        if isinstance(exception, commands.errors.NotOwner):
            embed = discord.Embed(title="Not allowed to use this command", color=discord.Color.red())
            await util.discord.reply(context, embed=embed)
            return

        # command wasn't found
        if isinstance(exception, commands.errors.CommandNotFound):
            user_command: str = exception.args[0].split('"')[1]

            # call help command if command ends with '.help'
            if user_command.endswith(".help"):
                help_cog = self.cogs["Help"]
                # pylint: disable-next=protected-access
                answer = help_cog._generate_help_specific_normal(user_command.replace(".help", ""))
                await context.message.reply(embed=answer)
                return

            embed = discord.Embed(title=f"Command '{user_command}' not found!\n")

            cmds: list[tuple[commands.Command, int]] = []
            for cmd in self.commands:
                dist = util.general.levenshtein_distance(cmd.name, user_command)
                if dist <= 2:
                    cmds.append((cmd, dist))

            if len(cmds) > 0:
                cmds.sort(key=lambda x:x[1])
                embed.add_field(name="Did you mean:", value="\n".join([f"- {cmd[0].name}" for cmd in cmds]))
                embed.color = discord.Color.orange()
            else:
                embed.color = discord.Color.dark_orange()

            await util.discord.reply(context, embed=embed)
            return

        # all other commands
        # code from https://stackoverflow.com/a/73706008/15436169
        user = await util.discord.get_bot().fetch_user(util.discord.get_user_id(context))
        full_error = traceback.format_exception(exception)
        msg_text = f"User {user} used command {util.discord.get_command_name(context)}:\n" \
                   + f"```py\n{''.join(full_error)}\n```"
        await util.discord.private_message(util.discord.get_owner_id(),
                                           msg_text)
        embed = discord.Embed(title="An error occured!",
                              color=discord.Color.red())
        message = await util.discord.get_reply(context)
        if message is not None:
            await message.edit(embed=embed)
        else:
            await util.discord.reply(context, embed=embed)

        return await super().on_command_error(context, exception)

    def send_to_channel(self, channel_id: int, text: str) -> discord.Message:
        """Send the given text to the given channel"""

        send_fut = asyncio.run_coroutine_threadsafe(self.get_channel(channel_id).send(text), self.loop)
        return send_fut.result()

# TODO:
# combine some parts of the mcserver-tools bot and roxy waifu bot
# fix /tc4 path
# write response message if argument is missing (implement in command_failed)
# tests (maybe with a second discord bot for testing purposes)
# add README
# create sing module with all music commands
# create command to set manga provider url
# fix manganato search for: oshi no ko, solo leveling
# create command to list manga with reading status

# pylint: disable=protected-access
if __name__ == "__main__":
    util.VolatileStorage["storage_file"] = STORAGE_FILE
    util.PersistentStorage._load_from_disk()

    util.VolatileStorage["cache_dir"] = CACHE_DIR
    os.makedirs(util.VolatileStorage["cache_dir"], exist_ok=True)

    util.VolatileStorage["temp_dir"] = TEMP_DIR
    shutil.rmtree(util.VolatileStorage["temp_dir"], ignore_errors=True)
    os.makedirs(util.VolatileStorage["temp_dir"], exist_ok=True)

    bot = DiscordBot()

    util.VolatileStorage["bot"] = bot

    bot.start_bot()

# pylint: enable=protected-access
