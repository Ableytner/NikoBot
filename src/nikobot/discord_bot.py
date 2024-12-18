"""A module containing the ``DiscordBot`` class"""

import traceback

import asyncio
import logging
import os

import discord as discordpy
from discord.ext import commands

from nikobot.util import discord, general, storage

logger = logging.getLogger("core")

class DiscordBot(commands.Bot):
    """The main ``discord.commands.Bot`` which is the center of the application"""

    def __init__(self) -> None:
        super().__init__(command_prefix = "niko.", help_command=None, intents = discordpy.Intents.all())

    def start_bot(self):
        """Start the discord bot"""

        self.run(os.environ["DISCORD_TOKEN"], log_handler=None)

    async def setup_hook(self) -> None:
        modules_to_load = []
        if "modules_to_load" in storage.VolatileStorage:
            modules_to_load = storage.VolatileStorage["modules_to_load"]
            del storage.VolatileStorage["modules_to_load"]

        storage.VolatileStorage["modules"] = []

        for module in modules_to_load:
            await self.load_extension(f"nikobot.modules.{module}")
            storage.VolatileStorage["modules"].append(module)
            logger.info(f"Loaded module {module}")

    async def on_ready(self):
        """Method called when the bot is ready"""

        logger.info(f"{self.user} is now online")

    async def on_command_error(self,
                               context: commands.context.Context,
                               exception: commands.errors.CommandError, /) -> None:
        # owner-only commands
        if isinstance(exception, commands.errors.NotOwner):
            embed = discordpy.Embed(title="Not allowed to use this command", color=discordpy.Color.red())
            await discord.reply(context, embed=embed)
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

            embed = discordpy.Embed(title=f"Command '{user_command}' not found!", color=discordpy.Color.red())

            cmds: list[tuple[commands.Command, int]] = []
            for cmd in self.commands:
                dist = general.levenshtein_distance(cmd.name, user_command)
                if dist <= 2:
                    cmds.append((cmd, dist))

            if len(cmds) > 0:
                cmds.sort(key=lambda x:x[1])
                embed.add_field(name="Did you mean:", value="\n".join([f"- {cmd[0].name}" for cmd in cmds]))
                embed.color = discordpy.Color.orange()
            else:
                embed.color = discordpy.Color.dark_orange()

            await discord.reply(context, embed=embed)
            return
        
        # command was misused by the user
        if isinstance(exception, commands.errors.UserInputError):
            if isinstance(exception, commands.MissingRequiredArgument):
                required_arg: str = exception.args[0].split(' ', maxsplit=1)[0]
                embed = discordpy.Embed(title=f"Missing required argument '{required_arg}'!", color=discordpy.Color.red())
                await discord.reply(context, embed=embed)
                return
            if isinstance(exception, commands.TooManyArguments):
                embed = discordpy.Embed(title=f"Too many arguments!", color=discordpy.Color.red())
                await discord.reply(context, embed=embed)
                return

        # all other commands
        # code from https://stackoverflow.com/a/73706008/15436169
        try:
            user = await discord.get_bot().fetch_user(discord.get_user_id(context))
            full_error = traceback.format_exception(exception)
            msg_text = f"User {user} used command {discord.get_command_name(context)}:\n" \
                    + f"```py\n{''.join(full_error[:1500])}\n```"
            await discord.private_message(discord.get_owner_id(),
                                            msg_text)
        except Exception:
            logger.warning("Couldn't notify owner about command error!")

        embed = discordpy.Embed(title="An error occured!",
                              color=discordpy.Color.red())
        message = await discord.get_reply(context)
        if message is not None:
            await message.edit(embed=embed)
        else:
            await discord.reply(context, embed=embed)

        return await super().on_command_error(context, exception)

    def send_to_channel(self, channel_id: int, text: str) -> discordpy.Message:
        """Send the given text to the given channel"""

        send_fut = asyncio.run_coroutine_threadsafe(self.get_channel(channel_id).send(text), self.loop)
        return send_fut.result()
