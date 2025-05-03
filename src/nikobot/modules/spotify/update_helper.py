"""Module which contains helper functions for spotify track difference calculation"""

from typing import TypeAlias

from abllib import log
from discord import Color, Embed, Message
from discord.interactions import InteractionMessage

from . import api_helper
from .cache import PlaylistCache
from .dclasses import TrackSet, Playlist

logger = log.get_logger("spotify.update_helper")

MessageType: TypeAlias = Message | InteractionMessage | None

async def get_current_track_ids(user_id: int, p_meta: Playlist, message: MessageType) -> list[str]:
    """return all track_ids in the all_playlist, sorted from oldest to newest"""

    track_ids = []
    cache = PlaylistCache(user_id)

    cached_tracks = cache.get(p_meta)
    if cached_tracks is not None:
        if message is not None:
            await message.edit(embed=Embed(title="Loading already present tracks from cache",
                                           description=f"{p_meta.name}: {p_meta.total_tracks} tracks",
                                           color=Color.blue()))
        logger.debug("using cached tracks for all_playlist")

        for t_id in cached_tracks:
            track_ids.append(t_id)
    else:
        if message is not None:
            await message.edit(embed=Embed(title="Loading tracks",
                                            description=f"{p_meta.name}: {p_meta.total_tracks} tracks",
                                            color=Color.blue()))

        async for t_meta in api_helper.get_tracks(user_id, p_meta.id):
            track_ids.append(t_meta[0])

        # sort from old to new
        track_ids.reverse()

    return track_ids

async def get_all_track_ids(user_id: int, playlist_metas: list[Playlist], message: MessageType) -> list[str]:
    """return all track_ids in the given playlists, sorted from oldest ot newest"""

    track_set = TrackSet()
    cache = PlaylistCache(user_id)

    # load saved tracks
    p_meta = await api_helper.get_saved_tracks_meta(user_id)
    cached_tracks = cache.get(p_meta)
    if cached_tracks is not None:
        if message is not None:
            await message.edit(embed=Embed(title="Loading already present tracks from cache",
                                           description=f"Liked songs: {p_meta.total_tracks} tracks",
                                           color=Color.blue()))
        logger.debug("using cached tracks for saved tracks")

        for t_meta in cached_tracks:
            track_set.add(*t_meta)
    else:
        if message is not None:
            await message.edit(embed=Embed(title="Loading tracks",
                                            description=f"Liked songs: {p_meta.total_tracks} tracks",
                                            color=Color.blue()))

        tracks_meta = []
        async for t_meta in api_helper.get_saved_tracks(user_id):
            tracks_meta.append(t_meta)
            track_set.add(*t_meta)

        cache.set(p_meta, tracks_meta)

    # load all other playlists
    for p_meta in playlist_metas:
        cached_tracks = cache.get(p_meta)
        if cached_tracks is not None:
            if message is not None:
                await message.edit(embed=Embed(title="Loading tracks from cache",
                                               description=f"{p_meta.name}: {p_meta.total_tracks} tracks",
                                               color=Color.blue()))
            logger.debug(f"using cached tracks for {p_meta.name}")

            for t_meta in cached_tracks:
                track_set.add(*t_meta)
        else:
            if message is not None:
                await message.edit(embed=Embed(title="Loading tracks",
                                               description=f"{p_meta.name}: {p_meta.total_tracks} tracks",
                                               color=Color.blue()))

            tracks_meta = []
            async for t_meta in api_helper.get_tracks(user_id, p_meta.id):
                tracks_meta.append(t_meta)
                track_set.add(*t_meta)

            cache.set(p_meta, tracks_meta)

    return track_set.ids()

def calculate_diff(saved_track_ids: list[str], updated_track_ids: list[str]) -> tuple[list[str], list[str]]:
    """
    Calculate the difference between the given track id lists.

    The given lists need to be sorted oldest-to-newest.

    Returns two arrays:
    * the track ids which need to be removed
    * the track ids which need to be added
    
    """

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
