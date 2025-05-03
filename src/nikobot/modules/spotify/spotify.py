"""contains the cog of the spotify module"""

import asyncio
from asyncio import sleep
from threading import Thread

from abllib import PersistentStorage
from abllib.log import get_logger
from discord import app_commands, Color, Embed
from discord.ext import commands

from . import api_helper, auth_helper, auth_server, update_helper
from .cache import PlaylistCache
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

        embed = Embed(title="Waiting for user to finish authenticating",
                      description="Check your direct messages for further instructions.",
                      color=Color.blue())
        await message.edit(embed=embed)

        embed = Embed(title="Registering Spotify account for use with nikobot.spotify commands",
                      description=f"Click the following link to complete authentication:\n{auth_url}",
                      color=Color.blue())
        embed.add_field(name=" ", value=" ", inline=False)
        embed.add_field(name="Note",
                        value="You have 5 minutes until registration times out.",
                        inline=False)
        await private_message(user_id, embed=embed)

        elapsed = 0
        while not auth_helper.is_authed(user_id) and elapsed < 60 * 5:
            await sleep(1)
            elapsed += 1

        if not auth_helper.is_authed(user_id) and elapsed >= 60 * 5:
            auth_helper.cancel_auth(user_id)
            await reply(ctx, embed=Embed(title="Registration timed out",
                                         color=Color.orange()))
            return

        # TODO: check if user cancelled authentication

        await message.edit(embed=Embed(title="Successfully registered with your Spotify account!",
                                       color=Color.green()))

    @grouped_hybrid_command(
        "deregister",
        "Deregister an users' Spotify account from the discord bot",
        command_group
    )
    async def deregister(self, ctx: commands.context.Context):
        """The discord command 'niko.spotify.deregister'"""

        user_id = get_user_id(ctx)

        if not auth_helper.is_authed(user_id):
            await reply(ctx, embed=Embed(title=REGISTER_MSG, color=Color.orange()))
            return

        del PersistentStorage[f"spotify.{user_id}"]
        PersistentStorage.save_to_disk()

        # the Spotify App can't be removed via the API
        # https://github.com/spotify/web-api/issues/600

        embed = Embed(title="Successfully deregistered your Spotify account from this disord bot",
                            description="If you change your mind, "
                                        "you can always re-register using the command 'niko.spotify.register'.",
                            color=Color.blue())
        embed.add_field(name=" ", value=" ", inline=False)
        embed.add_field(name="Note",
                        value="Click the following link to remove NikoBot from your Spotify Apps:\n"
                              "https://www.spotify.com/account/apps/",
                        inline=False)
        await reply(ctx, embed=embed)

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
        is_new_playlist = None

        if f"spotify.{user_id}.all_playlist.id" in PersistentStorage:
            try:
                all_playlist = await api_helper.get_playlist_meta(
                    user_id,
                    PersistentStorage[f"spotify.{user_id}.all_playlist.id"])
                message = await reply(ctx, embed=Embed(title=f"Updating existing playlist {all_playlist.name}",
                                                       color=Color.blue()))
                is_new_playlist = False
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
            is_new_playlist = True

        playlist_metas = await api_helper.get_playlists(user_id)
        # exclude all_playlist
        playlist_metas = [item for item in playlist_metas if item.id != all_playlist.id]
        updated_track_ids = await update_helper.get_all_track_ids(user_id, playlist_metas, message)

        current_track_ids = await update_helper.get_current_track_ids(user_id, all_playlist, message)

        await message.edit(embed=Embed(title="Calculating",
                                       description="Checking which songs to add",
                                       color=Color.blue()))
        to_remove, to_add = update_helper.calculate_diff(current_track_ids, updated_track_ids)
        # the newest track needs to be first
        to_add.reverse()

        await message.edit(embed=Embed(title="Updating your playlist",
                                       description=f"Removing {len(to_remove)} and adding {len(to_add)} tracks",
                                       color=Color.blue()))
        logger.info(f"Removing {len(to_remove)} and adding {len(to_add)} tracks")
        if len(to_remove) > 0:
            await api_helper.remove_tracks(user_id, all_playlist.id, to_remove)
        if len(to_add) > 0:
            await api_helper.add_tracks(user_id, all_playlist.id, to_add)

        # wait for spotify to finish processing
        await sleep(5)

        # request new snapshot_id
        all_playlist = await api_helper.get_playlist_meta(user_id, all_playlist.id)
        cache = PlaylistCache(user_id)
        cache.set(all_playlist, current_track_ids)

        title = "Successfully created new playlist" if is_new_playlist else "Successfully updated your playlist"
        embed = Embed(title=title,
                      description=f"Removed {len(to_remove)} and added {len(to_add)} tracks "
                                  f"to {all_playlist.name} for a total of {len(updated_track_ids)} tracks.",
                      color=Color.green())
        embed.add_field(name=" ", value=" ", inline=False)
        embed.add_field(name="Url",
                        value=f"https://open.spotify.com/playlist/{all_playlist.id}",
                        inline=False)
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
