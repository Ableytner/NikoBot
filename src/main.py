import os

import asyncio
import discord
from discord.ext import commands
import numpy

from nikobot import util

MODULES = ["general", "clear", "music", "avatar", "owner", "tc4.tc4"]

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
            user_command = exception.args[0].split('"')[1]
            answer = f"Command '{user_command}' not found!\n"

            cmds: list[tuple[commands.Command, int]] = []
            for cmd in self.commands:
                dist = levenshtein_distance(cmd.name, user_command)
                if dist <= 2:
                    cmds.append((cmd, levenshtein_distance(cmd.name, user_command)))
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

def levenshtein_distance(token1: str, token2: str) -> int:
    distances = numpy.zeros((len(token1) + 1, len(token2) + 1))

    for t1 in range(len(token1) + 1):
        distances[t1][0] = t1

    for t2 in range(len(token2) + 1):
        distances[0][t2] = t2

    a = 0
    b = 0
    c = 0

    for t1 in range(1, len(token1) + 1):
        for t2 in range(1, len(token2) + 1):
            if (token1[t1-1] == token2[t2-1]):
                distances[t1][t2] = distances[t1 - 1][t2 - 1]
            else:
                a = distances[t1][t2 - 1]
                b = distances[t1 - 1][t2]
                c = distances[t1 - 1][t2 - 1]
                
                if (a <= b and a <= c):
                    distances[t1][t2] = a + 1
                elif (b <= a and b <= c):
                    distances[t1][t2] = b + 1
                else:
                    distances[t1][t2] = c + 1

    return distances[len(token1)][len(token2)]

# to-do
# combine some parts of the mcserver-tools bot and roxy waifu bot

if __name__ == "__main__":
    bot = DiscordBot()

    util.bot = bot

    bot.start_bot()
