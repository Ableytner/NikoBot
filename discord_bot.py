import asyncio
from queue import Queue
import discord
from discord.ext import commands
import requests

class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix = 'niko.', help_command=None, intents = discord.Intents.all())

    def start_bot(self):
        """Start the discord bot"""

        with open("dc_token.txt", "r", encoding="utf8") as file:
            token = file.readlines()[0]
        self.run(token)

    async def setup_hook(self) -> None:
        await self.load_extension("general")
        await self.load_extension("clear")
        await self.load_extension("music")
        # await self.load_extension("test")

    async def on_ready(self):
        """Method called when the bot is ready"""

        print(f"{self.user} is now online")

    async def on_reaction_add(self, reaction: discord.reaction.Reaction, user: discord.member.Member):
        """Method called when a reaction is added to a comment"""

        if user.id == self.user.id:
            return

    def send_to_channel(self, channel_id: int, text: str):
        """Send the given text to the given channel"""

        send_fut = asyncio.run_coroutine_threadsafe(self.get_channel(channel_id).send(text), self.loop)
        self._messages[channel_id] = send_fut.result()

if __name__ == "__main__":
    DiscordBot().start_bot()

# to-do
# combine some parts of the mcserver-tools bot and roxy waifu bot
