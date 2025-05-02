"""Module which contains helper functions for spotify track difference calculation"""

from discord import Color, Embed, Message
from discord.interactions import InteractionMessage

from . import api_helper
from .dclasses import TrackSet

async def get_all_track_ids(user_id: str, playlist_ids: list[str], message: Message | InteractionMessage | None) -> list[str]:
    """return all track_ids in the given playlists, sorted from oldest ot newest"""

    updated_track_set = TrackSet()

    if message is not None:
        await message.edit(embed=Embed(title="Loading tracks",
                                       description="Liked Songs",
                                       color=Color.blue()))
    async for t_meta in api_helper.get_saved_tracks(user_id):
        updated_track_set.add(*t_meta)

    for p_id in playlist_ids:
        p_meta = await api_helper.get_playlist_meta(user_id, p_id)
        if message is not None:
            await message.edit(embed=Embed(title="Loading tracks",
                                           description=f"{p_meta.name}: {p_meta.total_tracks} tracks",
                                           color=Color.blue()))

        async for t_meta in api_helper.get_tracks(user_id, p_id):
            updated_track_set.add(*t_meta)

    return updated_track_set.ids()

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
