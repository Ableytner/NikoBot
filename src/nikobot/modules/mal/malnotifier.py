"""A module containing MyAnimeList-related commands"""

import logging
import os
from datetime import datetime, timedelta
from threading import Thread

import discord as discordpy
from discord import app_commands
from discord.ext import commands, tasks

from . import error, manganato_helper, mal_helper
from .mal_user import MALUser
from .manga import Manga
from ... import util

# pylint: disable=protected-access

logger = logging.getLogger("mal")

command_group = app_commands.Group(
    name="mal",
    description="The module for MyAnimeList-related commands"
)

class MALNotifier(commands.Cog):
    """A ``discord.commands.Cog`` containing MyAnimeList-related commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.users = []

    @util.discord.grouped_hybrid_command(
            name="manga",
            description="Search for a manga on MyAnimeList",
            command_group=command_group
    )
    async def manga(self, ctx: commands.context.Context | discordpy.interactions.Interaction, *title: list[str]):
        """The discord command 'niko.mal.manga'"""

        recombined_title = " ".join(["".join(item) for item in title])

        if recombined_title.isdecimal():
            mal_id = int(recombined_title)
        else:
            mal_id = mal_helper.search_for_manga(recombined_title)
            if mal_id is None:
                await util.discord.reply(ctx,
                                        embed=discordpy.Embed(title="Manga not found on MyAnimeList",
                                                            color=discordpy.Color.orange()))
                return

        manga = None

        user_id = util.discord.get_user_id(ctx)
        if util.VolatileStorage.contains(f"mal.user.{user_id}"):
            maluser: MALUser = util.VolatileStorage[f"mal.user.{user_id}"]
            maluser.fetch_manga_list()
            if mal_id in maluser.manga:
                manga = maluser.manga[mal_id]
                manga.fetch_chapters()

        if manga is None:
            try:
                manga = Manga.from_mal_id(mal_id)
            except error.MediaTypeError:
                await util.discord.reply(ctx,
                                         embed=discordpy.Embed(title="Currently only supports manga "
                                                             + "and not light novel/novel",
                                                             color=discordpy.Color.orange()))
                return

        # pylint: disable-next=redefined-outer-name
        embed, file = manga.to_embed()
        await util.discord.reply(ctx, embed=embed, file=file)

    @util.discord.grouped_hybrid_command(
        name="register",
        description="Register an existing MyAnimeList account for use with the discord bot",
        command_group=command_group
    )
    async def register(self, ctx: commands.context.Context | discordpy.interactions.Interaction, username: str):
        """The discord command 'niko.mal.register'"""

        user_id = util.discord.get_user_id(ctx)

        if util.VolatileStorage.contains(f"mal.user.{user_id}"):
            await util.discord.reply(ctx, embed=discordpy.Embed(title="You are already registered",
                                                              color=discordpy.Color.orange()))
            return

        message = await util.discord.reply(ctx, embed=discordpy.Embed(title="Fetching manga list from MyAnimeList",
                                                                    color=discordpy.Color.blue()))

        try:
            maluser = MALUser(username.lower(), user_id)
            await message.edit(embed=discordpy.Embed(title="Fetching manga list from MyAnimeList",
                                                   color=discordpy.Color.blue()))
            maluser.fetch_manga_list()
            await message.edit(embed=discordpy.Embed(title="Fetching manga chapters from Manganato",
                                                   color=discordpy.Color.blue()))
            maluser.fetch_manga_chapters()
        except error.UserNotFound:
            await message.edit(embed=discordpy.Embed(title="MyAnimeList user wasn't found",
                                                   color=discordpy.Color.dark_orange()))
            return

        util.VolatileStorage[f"mal.user.{user_id}"] = maluser
        await message.edit(embed=discordpy.Embed(title="Successfully registered for new release notifications",
                                               color=discordpy.Color.blue()))

        # force-update the user once after registration
        await self.notify_user(user_id, maluser)

    @util.discord.grouped_hybrid_command(
        name="deregister",
        description="Deregister the connected MyAnimeList account from your discord account",
        command_group=command_group
    )
    async def deregister(self, ctx: commands.context.Context | discordpy.interactions.Interaction):
        """The discord command 'niko.mal.dergister'"""

        if util.discord.is_slash_command(ctx):
            user_id = ctx.user.id
        else:
            user_id = ctx.author.id

        if not util.VolatileStorage.contains(f"mal.user.{user_id}"):
            await util.discord.reply(ctx,
                                     embed=discordpy.Embed(title="You are not yet registered",
                                                         color=discordpy.Color.orange()))
            return

        del util.VolatileStorage[f"mal.user.{user_id}"]
        await util.discord.reply(ctx,
                                 embed=discordpy.Embed(title="Successfully deregistered from release notifications",
                                                     color=discordpy.Color.blue()))

    @util.discord.grouped_hybrid_command(
        name="update",
        description="Check for new manga chapters for the MyAnimeList account connected to your discord account",
        command_group=command_group
    )
    async def update(self, ctx: commands.context.Context | discordpy.interactions.Interaction):
        """The discord command 'niko.mal.update'"""

        if util.discord.is_slash_command(ctx):
            user_id = ctx.user.id
        else:
            user_id = ctx.author.id

        if not util.VolatileStorage.contains(f"mal.user.{user_id}"):
            await util.discord.reply(ctx,
                                     embed=discordpy.Embed(title="You are not yet registered",
                                                         color=discordpy.Color.orange()))
            return

        embed = discordpy.Embed(title="Checking for new chapters...",
                              color=discordpy.Color.blue())
        embed.add_field(name="\u200b",
                        value="Please wait a few minutes",
                        inline=True)
        message = await util.discord.reply(ctx, embed=embed)

        maluser = util.VolatileStorage[f"mal.user.{user_id}"]
        await self.notify_user(int(user_id), maluser)

        await message.edit(embed=discordpy.Embed(title="Finished checking!",
                                               color=discordpy.Color.blue()))

    @tasks.loop(hours=1, reconnect=True, name="notify-users-task")
    async def notify_users(self):
        """A method responsible for notifying users if a new manga chapter was released"""

        if not util.VolatileStorage.contains("mal.user"):
            return

        for user_id, maluser in util.VolatileStorage["mal.user"].items():
            if not isinstance(user_id, str): raise TypeError()
            if not isinstance(maluser, MALUser): raise TypeError()

            await self.notify_user(int(user_id), maluser)

    async def notify_user(self, user_id: int, maluser: MALUser) -> None:
        """Notify the user if any of his ``Manga`` got a new chapter"""

        if not isinstance(user_id, int): raise TypeError()
        if not isinstance(maluser, MALUser): raise TypeError()

        maluser.fetch_manga_list()

        for manga in maluser.manga.values():
            if not isinstance(manga, Manga): raise TypeError()

            if manga._time_next_notify < datetime.now():
                await self.notify_manga(int(user_id), manga)

        maluser.save_to_storage()

    async def notify_manga(self, user_id: int, manga: Manga) -> None:
        """Notify the user if the given ``Manga`` received a new chapter"""

        if not isinstance(user_id, int): raise TypeError()
        if not isinstance(manga, Manga): raise TypeError()

        if not manga.fetch_chapters():
            return

        if manga._chapters_total > manga._chapters_read \
            and manga._chapters_total > manga._chapters_last_notified:
            # pylint: disable-next=redefined-outer-name
            embed, file = manga.to_embed()

            new_chapters = manga._chapters_total - manga._chapters_read
            if new_chapters == 1:
                embed.title += "  |  1 new chapter"
            else:
                embed.title += f"  |  {new_chapters} new chapters"

            await util.discord.private_message(user_id, embed=embed, file=file)

            manga._chapters_last_notified = manga._chapters_total
            manga._time_next_notify = datetime.now() + timedelta(hours=12)

    def import_users(self):
        """Import all MALUsers from ``util.PersistentStorage``"""

        c = 0
        if util.PersistentStorage.contains("mal.user"):
            for user_id, maluser_json in util.PersistentStorage["mal.user"].items():
                maluser = MALUser.from_export(int(user_id), maluser_json)
                maluser.fetch_manga_chapters()
                util.VolatileStorage[f"mal.user.{user_id}"] = maluser
                c += 1
        logger.info(f"Finished importing {c} MAL user(s)")

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    util.VolatileStorage["mal.CLIENT-ID"] = os.environ["MAL_CLIENT_ID"]

    mal_helper._setup()
    manganato_helper._setup()

    cog = MALNotifier(bot)

    Thread(target=cog.import_users, daemon=True).start()

    cog.notify_users.start()

    await bot.add_cog(cog)

# pylint: enable=protected-access
