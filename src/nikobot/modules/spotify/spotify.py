"""contains the cog of the spotify module"""

from asyncio import sleep
import threading
from threading import Thread

from abllib import PersistentStorage, VolatileStorage, CacheStorage, onexit
from abllib.log import get_logger
from discord import app_commands, Color, Embed
from discord.ext import commands, tasks

from . import api_helper, auth_helper, auth_server, update_helper
from .cache import PlaylistCache
from .dclasses import Playlist, Track
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
        while not auth_helper.is_authed(user_id) and f"spotify.auth.{user_id}" in VolatileStorage and elapsed < 60 * 5:
            await sleep(1)
            elapsed += 1

        if auth_helper.is_authed(user_id):
            # auth was successful

            # verify that requests actually work
            try:
                p_meta = await api_helper.create_playlist(user_id, "temp")
                await api_helper.delete_playlist(user_id, p_meta.id)
            except ApiResponseError as ex:
                if ex.status_code == 403:
                    # app is in development mode and user isn't added to User Management
                    auth_helper.cancel_auth(user_id)
                    del PersistentStorage[f"spotify.{user_id}"]
                    embed = Embed(title="You are not authorized",
                                  description="Contact the bot's owner for adding you to Spotify User Management.",
                                  color=Color.orange())
                    embed.add_field(name=" ", value=" ", inline=False)
                    embed.add_field(name="Info",
                                    value="You can read more about why this is needed here:\n" \
                                          "https://developer.spotify.com/documentation/web-api/concepts/quota-modes",
                                    inline=False)
                    await message.edit(embed=embed)
                    return

                raise

            await message.edit(embed=Embed(title="Successfully registered with your Spotify account!",
                                           color=Color.green()))
        elif f"spotify.auth.{user_id}" not in VolatileStorage:
            # user cancelled auth
            await message.edit(embed=Embed(title="Registration was cancelled",
                                           color=Color.orange()))
        elif elapsed >= 60 * 5:
            auth_helper.cancel_auth(user_id)
            await message.edit(embed=Embed(title="Registration timed out",
                                           color=Color.orange()))

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

        is_new_playlist = True

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

        if is_new_playlist:
            all_playlist = await api_helper.create_playlist(user_id, "🌎 everything")
            PersistentStorage[f"spotify.{user_id}.all_playlist.id"] = all_playlist.id
            message = await reply(ctx, embed=Embed(title=f"Creating new playlist {all_playlist.name}",
                                                   color=Color.blue()))

        await update_helper.run(user_id, True)

        embed = Embed(
            title="Successfully created your new playlist" if is_new_playlist else "Successfully updated your playlist",
            description="The playlist is automatically updated every 15 minutes.",
            color=Color.green()
        )
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

    @tasks.loop(minutes=15, reconnect=True, name="update-all-playlists-task")
    async def update_all_playlists(self):
        """Update all all_playlists every 15 minutes"""

        if "spotify" not in PersistentStorage:
            # no user is registered
            return

        for user_id in PersistentStorage["spotify"].keys():
            # ignore all entries that aren't user ids
            if user_id.isdigit():
                try:
                    await update_helper.run(int(user_id), True)
                except ApiResponseError as err:
                    logger.exception(err)

def import_cache():
    """Import playlist cache from PersistentStorage"""

    if "spotify" not in PersistentStorage:
        return

    for user_id in PersistentStorage["spotify"].keys():
        # ignore all entries that aren't user ids
        if user_id.isdigit() and "cache" in PersistentStorage[f"spotify.{user_id}"]:
            # load cache for user
            cache = PlaylistCache.get_instance(user_id)

            for p_id in PersistentStorage[f"spotify.{user_id}.cache"].keys():
                tracks = []
                for item in PersistentStorage[f"spotify.{user_id}.cache.{p_id}.tracks"]:
                    track = Track(
                        item[0],
                        item[1] if len(item) > 1 else None
                    )
                    tracks.append(track)
                cache.set(
                    Playlist(
                        "",
                        p_id,
                        len(tracks),
                        PersistentStorage.get(f"spotify.{user_id}.cache.{p_id}.snapshot_id")
                    ),
                    tracks
                )

def export_cache():
    """Export playlist cache to PersistentStorage"""

    for user_id in CacheStorage["spotify"].keys():
        # ignore all entries that aren't user ids
        if user_id.isdigit() and "cache" in CacheStorage[f"spotify.{user_id}"]:
            # save cache for user
            logger.debug(f"Exporting spotify playlist cache for user {user_id}")
            cache = PlaylistCache.get_instance(user_id)

            for p_id in CacheStorage[cache.key].keys():
                key = f"{cache.key}.{p_id}"

                snapshot_id = CacheStorage.get(f"{key}.snapshot_id")
                if snapshot_id is not None:
                    PersistentStorage[f"{key}.snapshot_id"] = snapshot_id

                tracks = []
                for track in CacheStorage[f"{key}.tracks"]:
                    track: Track
                    if p_id == PersistentStorage[f"spotify.{user_id}.all_playlist.id"]:
                        tracks.append(track.id)
                    else:
                        tracks.append([
                            track.id,
                            track.added_at
                        ])
                PersistentStorage[f"{key}.tracks"] = tracks

    PersistentStorage.save_to_disk()

    logger.info("Finished exporting spotify playlist cache")

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    cog = Spotify(bot)

    import_cache()

    cog.update_all_playlists.start()

    Thread(target=auth_server.run_http_server, daemon=True).start()

    # signal.signal callbacks don't work in subthreads (only occurs in tests anyways)
    if threading.current_thread() is threading.main_thread():
        onexit.register("export_spotify_cache", export_cache)

    await bot.add_cog(cog)
