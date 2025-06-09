"""Module which contains helper functions for spotify track difference calculation"""

from asyncio import sleep
from typing import TypeAlias

from abllib import log, PersistentStorage
from abllib.error import WrongTypeError
from discord import Color, Embed, Message
from discord.interactions import InteractionMessage

from . import api_helper
from .cache import PlaylistCache
from .dclasses import Track, TrackSet
from ...util import discord

logger = log.get_logger("spotify.update_helper")

MessageType: TypeAlias = Message | InteractionMessage | None

# pylint: disable=broad-exception-raised, too-many-statements

async def run(user_id: int, notify_user: bool = True) -> None:
    """Check if any playlist cnahged, and update all_playlist accordingly"""

    if not isinstance(user_id, int): raise WrongTypeError.with_values(user_id, int)

    if f"spotify.{user_id}.all_playlist.id" not in PersistentStorage:
        raise Exception(f"Expected all_playlist to exist for user {user_id}")

    playlists = await api_helper.get_playlists(user_id)
    liked_songs_playlist = await api_helper.get_saved_tracks_meta(user_id)
    all_playlist = await api_helper.get_playlist_meta(
        user_id,
        PersistentStorage[f"spotify.{user_id}.all_playlist.id"]
    )

    cache = PlaylistCache.get_instance(user_id)

    if cache.get(all_playlist) is None:
        raise Exception("all_playlist changed since last cache update,"
                        " which means the user added/deleted a song manually")

    cached_playlists = []
    changed_playlists = []

    for playlist in playlists:
        # ignore all_playlist
        if playlist.id != all_playlist.id:
            cached = cache.get(playlist)
            if cached is not None:
                # cache hit
                cached_playlists.append(playlist)
            else:
                # cache miss or is not up-to-date
                changed_playlists.append(playlist)

    # TODO: check Liked Songs
    if len(changed_playlists) == 0:
        # yay, nothing changed and we can exit early
        return

    new_tracks_set = TrackSet()

    # load tracks from cached playlists
    if notify_user:
        message = await discord.private_message(
            user_id,
            embed=Embed(
                title="Loading tracks from cache",
                description=f"Loading tracks from {len(cached_playlists)} unchanged playlists",
                color=Color.blue()
            )
        )
    for playlist in cached_playlists:
        for track in cache.get(playlist):
            new_tracks_set.add(track)

    # fetch tracks from changed playlists
    for playlist in changed_playlists:
        if notify_user:
            await message.edit(embed=Embed(
                    title="Loading tracks",
                    description=f"{playlist.name}: {playlist.total_tracks} tracks",
                    color=Color.blue()
                )
            )
        tracks = []
        async for track in api_helper.get_tracks(user_id, playlist.id):
            new_tracks_set.add(track)
            tracks.append(track)
        # order doesn't matter because its sorted by timestamp after
        cache.set(playlist, tracks)

    # load / fetch saved tracks ("Liked Songs")
    cached_tracks = cache.get(liked_songs_playlist)
    if cached_tracks is not None:
        # cache hit
        if notify_user:
            await message.edit(
                embed=Embed(
                    title="Loading tracks from cache",
                    description=f"{liked_songs_playlist.name}: {liked_songs_playlist.total_tracks} tracks",
                    color=Color.blue()
                )
            )
        for t_meta in cached_tracks:
            new_tracks_set.add(t_meta)
    else:
        # cache miss or is not up-to-date
        if notify_user:
            await message.edit(embed=Embed(
                title="Loading tracks",
                description=f"{liked_songs_playlist.name}: {liked_songs_playlist.total_tracks} tracks",
                color=Color.blue()
            )
        )
        tracks = []
        async for track in api_helper.get_saved_tracks(user_id):
            new_tracks_set.add(track)
            tracks.append(track)
        # update cache
        cache.set(liked_songs_playlist, tracks)

    # load / fetch track_ids in all_playlist
    current_tracks: list[Track] = []
    cached = cache.get(all_playlist)
    if cached is not None:
        # cache hit
        if notify_user:
            await message.edit(embed=Embed(
                    title="Loading tracks from cache",
                    description=f"{all_playlist.name}: {all_playlist.total_tracks} tracks",
                    color=Color.blue()
                )
            )
        for track in cached:
            current_tracks.append(track)
        # the cached tracks are already sorted correctly
    else:
        # cache miss
        if notify_user:
            await message.edit(embed=Embed(
                    title="Loading tracks",
                    description=f"{all_playlist.name}: {all_playlist.total_tracks} tracks",
                    color=Color.blue()
                )
            )
        async for track in api_helper.get_tracks(user_id, playlist.id):
            current_tracks.append(track)
        # sort from old to new
        current_tracks.reverse()
        # don't cache here, because we do that later after the update

    if notify_user:
        await message.edit(
            embed=Embed(
                title="Calculating",
                description="Checking which songs to add / remove",
                color=Color.blue()
            )
        )
    to_remove, to_add = calculate_diff(new_tracks_set.ids(), [item.id for item in current_tracks])

    if notify_user:
        await message.edit(
            embed=Embed(
                title="Updating your playlist",
                description=f"Removing {len(to_remove)} and adding {len(to_add)} tracks",
                color=Color.blue()
            )
        )
    logger.info(f"Removing {len(to_remove)} and adding {len(to_add)} tracks")
    if len(to_remove) > 0:
        # track order doesn't matter when removing
        await api_helper.remove_tracks(user_id, all_playlist.id, to_remove)
    if len(to_add) > 0:
        # the newest track needs to be first
        to_add.reverse()
        await api_helper.add_tracks(user_id, all_playlist.id, to_add)

    # wait for spotify to finish processing
    await sleep(5)

    # request new snapshot_id for all_playlist
    all_playlist = await api_helper.get_playlist_meta(user_id, all_playlist.id)
    cache = PlaylistCache.get_instance(user_id)
    cache.set(all_playlist, new_tracks_set.tracks())

    if notify_user:
        embed = Embed(
            title="Successfully updated your playlist",
            description=f"Removed {len(to_remove)} and added {len(to_add)} tracks to {all_playlist.name}"
                        f" for a total of {len(new_tracks_set.tracks())} tracks.",
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

def calculate_diff(saved_track_ids: list[str], updated_track_ids: list[str]) -> tuple[list[str], list[str]]:
    """
    Calculate the difference between the given track id lists.

    The given lists need to be sorted oldest-to-newest.

    Returns two arrays:
    * the track ids which need to be removed
    * the track ids which need to be added
    
    """

    # TODO: convert from str ids to Track objects

    to_remove = []

    offset = 0
    last_c = 0
    # pylint: disable-next=consider-using-enumerate
    for c in range(len(saved_track_ids)):
        last_c = c

        if c + offset > len(updated_track_ids) - 1:
            # we have exhausted all updated tracks
            to_remove += saved_track_ids[c:]
            break

        if saved_track_ids[c] != updated_track_ids[c + offset]:
            # remove the mismatching track
            to_remove.append(saved_track_ids[c])
            offset -= 1
    else:
        # if the loop completed without break
        last_c += 1

    # add remaining new tracks
    to_add = updated_track_ids[last_c + offset:]

    return (to_remove, to_add)
