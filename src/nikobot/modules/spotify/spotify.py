"""contains the cog of the spotify module"""

import asyncio
from asyncio import sleep
from threading import Thread

from abllib import PersistentStorage
from abllib.log import get_logger
from discord import app_commands, Color, Embed
from discord.ext import commands

from . import api_helper, auth_helper, auth_server, update_helper
from .error import ApiResponseError
from ...util.discord import grouped_hybrid_command, reply, get_user_id, private_message

logger = get_logger("spotify")

REGISTER_MSG = "You are not yet registered! Use the command 'niko.spotify.register' first"

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

    @grouped_hybrid_command(
        "all_playlist",
        "Create or update a playlist with all your songs from every playlist you created",
        command_group
    )
    async def all_playlist(self, ctx: commands.context.Context):
        """The discord command 'niko.spotify.all_playlist'"""

        user_id = get_user_id(ctx)

        if not auth_helper.is_authed(user_id):
            await reply(ctx, embed=Embed(title=REGISTER_MSG, color=Color.orange()))
            return

        # to make pylint happy
        message = None

        if f"spotify.{user_id}.all_playlist.id" in PersistentStorage:
            try:
                all_playlist = await api_helper.get_playlist_meta(
                    user_id,
                    PersistentStorage[f"spotify.{user_id}.all_playlist.id"])
                message = await reply(ctx, embed=Embed(title=f"Updating existing playlist {all_playlist.name}",
                                                       color=Color.blue()))
            except ApiResponseError as err:
                if err.status_code == 404:
                    # remove playlist if it wasn't found
                    del PersistentStorage[f"spotify.{user_id}.all_playlist.id"]
                else:
                    raise

        if f"spotify.{user_id}.all_playlist.id" not in PersistentStorage:
            all_playlist = await api_helper.create_playlist(user_id, "🌎 everything")
            PersistentStorage[f"spotify.{user_id}.all_playlist.id"] = all_playlist.id
            message = await reply(ctx, embed=Embed(title=f"Creating new playlist {all_playlist.name}",
                                                   color=Color.blue()))

        playlist_ids = await api_helper.get_playlist_ids(user_id)
        # remove all_playlist
        playlist_ids.remove(all_playlist.id)
        updated_track_ids = await update_helper.get_all_track_ids(user_id, playlist_ids, message)

        current_track_ids = await update_helper.get_current_track_ids(user_id, all_playlist, message)

        await message.edit(embed=Embed(title="Calculating",
                                       description="Checking which songs to add",
                                       color=Color.blue()))
        to_remove, to_add = update_helper.calculate_diff(current_track_ids, updated_track_ids)
        # the newest track needs to be first
        to_add.reverse()

        await message.edit(embed=Embed(title=f"Removing {len(to_remove)} and adding {len(to_add)} tracks",
                                        color=Color.blue()))
        if len(to_remove) > 0:
            await api_helper.remove_tracks(user_id, all_playlist.id, to_remove)
        if len(to_add) > 0:
            await api_helper.add_tracks(user_id, all_playlist.id, to_add)

        embed = Embed(title="Successfully updated your playlist",
                      description=f"Removed {len(to_remove)} and added {len(to_add)} tracks "
                                  f"to {all_playlist.name} for a total of {len(updated_track_ids)} tracks",
                      color=Color.green())
        embed.add_field(name=" ", value=" ", inline=False)
        embed.add_field(name="Note",
                        value="Local tracks are not supported by the Spotify Web API, so they were ignored.",
                        inline=False)
        embed.add_field(name=" ", value=" ", inline=False)
        embed.add_field(name="Note",
                        value="Do not delete the playlist on your own, use niko.spotify.all_playlist_remove instead!",
                        inline=False)
        await message.edit(embed=embed)

    @grouped_hybrid_command(
        "all_playlist_remove",
        "Remove the playlist created by niko.spotify.all_playlist",
        command_group
    )
    async def all_playlist_remove(self, ctx: commands.context.Context):
        """The discord command 'niko.spotify.all_playlist_remove'"""

        user_id = get_user_id(ctx)

        if not auth_helper.is_authed(user_id):
            await reply(ctx, embed=Embed(title=REGISTER_MSG, color=Color.orange()))
            return

        if f"spotify.{user_id}.all_playlist.id" in PersistentStorage:
            await api_helper.delete_playlist(user_id, PersistentStorage[f"spotify.{user_id}.all_playlist.id"])
            del PersistentStorage[f"spotify.{user_id}.all_playlist.id"]

        await reply(ctx, embed=Embed(title="Successfully deleted the playlist",
                                     color=Color.green()))

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    cog = Spotify(bot)

    # start http server
    def _start_http_server():
        def _completion_func(*args):
            fut = asyncio.ensure_future(auth_helper.complete_auth(*args), loop=bot.loop)
            return fut.result()

        auth_server.run_http_server(_completion_func)
    Thread(target=_start_http_server, daemon=True).start()

    await bot.add_cog(cog)
