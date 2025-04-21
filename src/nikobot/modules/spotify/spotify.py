"""contains the cog of the spotify module"""

from asyncio import sleep
from threading import Thread

from abllib import VolatileStorage, PersistentStorage
from abllib.log import get_logger
from discord import app_commands, Color, Embed
from discord.ext import commands

from . import api_helper, auth_helper, auth_server
from ...util.discord import grouped_hybrid_command, reply, get_user_id, private_message

logger = get_logger("spotify")

command_group = app_commands.Group(
    name="spotify",
    description="The module for Spotify-related commands"
)

class Spotify(commands.Cog):
    """The module for Spotify-related commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @grouped_hybrid_command(
        "register",
        "Register an existing Spotify account for use with the discord bot",
        command_group
    )
    async def register(self, ctx: commands.context.Context):
        """The discord command 'niko.spotify.register'"""

        user_id = get_user_id(ctx)

        if auth_helper.is_authed(user_id):
            await reply(ctx, embed=Embed(title="You are already registered",
                                         color=Color.orange()))
            return

        message = await reply(ctx, embed=Embed(title="Preparing for spotify auth",
                                               color=Color.blue()))

        auth_url = auth_helper.auth(user_id)

        reply_embed = Embed(title="Waiting for user to finish authenticating",
                            description="Check your direct messages for further instructions.",
                            color=Color.blue())
        await message.edit(embed=reply_embed)
        
        auth_url_embed = Embed(title="Registering Spotify account for use with nikobot.spotify commands",
                               description="Click the following link to complete authentication:\n"
                                           + f"{auth_url}\n"
                                           + "You have 5 minutes until registration times out.")
        await private_message(user_id, embed=auth_url_embed)

        elapsed = 0
        while not auth_helper.is_authed(user_id) and elapsed < 60 * 5:
            await sleep(1)
            elapsed += 1
        
        if not auth_helper.is_authed(user_id) and elapsed >= 60 * 5:
            auth_helper.cancel_auth()
            await reply(ctx, embed=Embed(title="Registration timed out",
                                         color=Color.orange()))
            return

        # TODO: check if user cancelled authentication

        await message.edit(embed=Embed(title="Successfully registered with your spotify account!",
                                       color=Color.green()))

    # TODO: deregister command + deregister spotify access?

    # TODO: all_playlist command

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    cog = Spotify(bot)

    # start http server
    Thread(target=lambda: auth_server.run_http_server(auth_helper.complete_auth), daemon=True).start()

    await bot.add_cog(cog)
