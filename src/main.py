import os

import asyncio
import discord
from discord.ext import commands

from nikobot import util

MODULES = ["general", "help", "clear", "music", "avatar", "owner", "tc4.tc4", "malnotifier.malnotifier"]

class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix = 'niko.', help_command=None, intents = discord.Intents.all())
        if not os.path.exists("cache"):
            os.mkdir("cache")

    def start_bot(self):
        """Start the discord bot"""

        with open("dc_token.txt", "r", encoding="utf8") as file:
            token = file.readlines()[0]
        self.run(token)

    async def setup_hook(self) -> None:
        for module in MODULES:
            await self.load_extension(f"nikobot.modules.{module}")

    async def on_ready(self):
        """Method called when the bot is ready"""

        print(f"{self.user} is now online")

    async def on_reaction_add(self, reaction: discord.reaction.Reaction, user: discord.member.Member):
        """Method called when a reaction is added to a comment"""

        if user.id == self.user.id:
            return

    async def on_command_error(self, context: commands.context.Context, exception: commands.errors.CommandError, /) -> None:
        if isinstance(exception, commands.errors.CommandNotFound):
            user_command: str = exception.args[0].split('"')[1]

            if user_command.endswith(".help"):
                help_cog = self.cogs["Help"]
                answer = help_cog._generate_help_specific_normal(user_command.replace(".help", ""))
                await context.message.reply(embed=answer)
                return

            answer = f"Command '{user_command}' not found!\n"

            cmds: list[tuple[commands.Command, int]] = []
            for cmd in self.commands:
                dist = util.general.levenshtein_distance(cmd.name, user_command)
                if dist <= 2:
                    cmds.append((cmd, dist))
            if len(cmds) > 0:
                answer += "Did you mean:"
                cmds.sort(key=lambda x:x[1])
                for cmd in cmds:
                    answer += f"\n* {cmd[0].name}"
            await context.message.reply(answer)
            return

        return await super().on_command_error(context, exception)

    def send_to_channel(self, channel_id: int, text: str) -> discord.Message:
        """Send the given text to the given channel"""

        send_fut = asyncio.run_coroutine_threadsafe(self.get_channel(channel_id).send(text), self.loop)
        return send_fut.result()

# to-do
# combine some parts of the mcserver-tools bot and roxy waifu bot

if __name__ == "__main__":
    bot = DiscordBot()

    util.VolatileStorage["bot"] = bot

    bot.start_bot()
