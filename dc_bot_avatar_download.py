import asyncio
from queue import Queue
import discord
from discord.ext import commands
import requests

class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix = 'mc.', help_command = None,
                         intents = discord.Intents.all())

        self._cogs = []
        for cog in self._cogs:
            cog.setup(self)

    def start(self):
        """Start the discord bot"""

        with open("dc_token.txt", "r", encoding="utf8") as file:
            token = file.readlines()[0]
        self.run(token)

    async def on_ready(self):
        """Method called when the bot is ready"""

        print(f"{self.user} is now online")

    async def on_reaction_add(self, reaction, user):
        """Method called when a reaction is added to a comment"""

        print(user.name)
        if user.name == str(self.user):
            return
        await self.cogs["BotCommands"].on_reaction(reaction, user)

    @commands.command()
    async def UwU(self, ctx):
        """Return the gesture"""

        await ctx.send("UwU")

    def send(self, channel_id, text):
        """Send the given text to the given channel"""

        if channel_id in self._messages \
           and len(self._messages[channel_id].content) + 2 + len(text) < 2000:
            new_text = f"{self._messages[channel_id].content}\n{text}"
            edit_fut = asyncio.run_coroutine_threadsafe(self._messages[channel_id] \
                              .edit(content=new_text), self.loop)
            edit_fut.result()
        else:
            while len(text) > 0:
                send_fut = asyncio.run_coroutine_threadsafe(self.get_channel(channel_id) \
                                  .send(text[0:1999:1]), self.loop)
                self._messages[channel_id] = send_fut.result()
                text = text[2000::1]

    def _handle_server(self, channel_id: int, queue: Queue):
        msg_text = queue.get()
        while not queue.empty():
            while len(msg_text) >= 2000:
                self.send(channel_id, msg_text[0:1999:1])
                msg_text = msg_text[2000::1]
            new_msg_text = queue.get()
            if len(msg_text + new_msg_text) + 2 > 2000:
                self.send(channel_id, msg_text)
                msg_text = new_msg_text
            else:
                msg_text += f"\n{new_msg_text}"
        if len(msg_text) > 0:
            self.send(channel_id, msg_text)

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        print(message.content)
        # Get the user's avatar URL
        user: discord.member.Member = message.mentions[0]
        avatar_url = user.avatar.url

        # Download the user's avatar
        response = requests.get(avatar_url)
        if response.status_code == 200:
            with open('avatar.png', 'wb') as f:
                f.write(response.content)
            await message.channel.send('Avatar downloaded!')
        else:
            await message.channel.send('Failed to download avatar.')

if __name__ == "__main__":
    DiscordBot().start()

# to-do
# create a AblBot, combining some parts of the mcserver-tools bot, roxy waifu bot and this function
# check why message.content is always empty
# add the image to the bot's reply
# set the image file name to the correct username, and delete file after sending
