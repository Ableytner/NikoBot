"""A module containing MyAnimeList-related commands"""

import os
from asyncio import sleep
from datetime import datetime, timedelta
from threading import Thread

import discord as discordpy
import requests
from abllib import fs
from abllib.log import get_logger
from abllib.storage import PersistentStorage, VolatileStorage
from discord import Color, Embed, File, app_commands
from discord.ext import commands, tasks
from PIL import Image, ImageDraw

from ... import util
from . import error, mal_helper, manganato_helper, natomanga_helper
from .mal_user import MALUser
from .manga import Manga

# pylint: disable=protected-access

logger = get_logger("mal")

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
    async def manga(self, ctx: commands.context.Context | discordpy.interactions.Interaction, title: str):
        """The discord command 'niko.mal.manga'"""

        user_id = util.discord.get_user_id(ctx)
        manga = await self.get_manga(title, user_id, ctx)

        # pylint: disable-next=redefined-outer-name
        embed, file = manga.to_embed()
        await util.discord.reply(ctx, embed=embed, file=file)

    @util.discord.grouped_hybrid_command(
            name="palette",
            description="Search for a manga on MyAnimeList and display its dominant colors",
            command_group=command_group
    )
    async def palette(self, ctx: commands.context.Context | discordpy.interactions.Interaction, title: str):
        """The discord command 'niko.mal.palette'"""

        user_id = util.discord.get_user_id(ctx)
        manga = await self.get_manga(title, user_id, ctx)

        cover_image = Image.open(manga.picture_file())
        dominant_colors = manga.get_dominant_colors(10)

        # general size variables
        orig_size = cover_image.size
        palette_size = (orig_size[0], (orig_size[1] // 5))
        size = (orig_size[0], orig_size[1] + palette_size[1])
        slice_width = palette_size[0] // len(dominant_colors)

        palette_img = Image.new("RGB", size)

        # paste the cover image
        palette_img.paste(cover_image)

        d = ImageDraw.Draw(palette_img)
        for c, color in enumerate(dominant_colors):
            shape = [(slice_width * c, orig_size[1]), ((slice_width * c) + slice_width, size[1])]
            d.rectangle(shape, color.rgb())

        path = fs.absolute(VolatileStorage["cache_dir"], "mal", f"{manga.mal_id}_palette.png")
        palette_img.save(path)

        embed = Embed(title=manga.title,
                      color=Color.from_rgb(*manga.get_color().rgb()))
        embed.set_image(url=f"attachment://{os.path.basename(path)}")
        await util.discord.reply(ctx, embed=embed, file=File(path))

    @util.discord.grouped_hybrid_command(
        name="register",
        description="Register an existing MyAnimeList account for use with the discord bot",
        command_group=command_group
    )
    async def register(self, ctx: commands.context.Context | discordpy.interactions.Interaction, username: str):
        """The discord command 'niko.mal.register'"""

        user_id = util.discord.get_user_id(ctx)

        if VolatileStorage.contains(f"mal.user.{user_id}"):
            await util.discord.reply(ctx, embed=Embed(title="You are already registered", color=Color.orange()))
            return

        message = await util.discord.reply(ctx, embed=Embed(title="Fetching user from MyAnimeList", color=Color.blue()))

        try:
            maluser = MALUser(username.lower(), user_id)

            await message.edit(embed=Embed(title="Fetching manga list from MyAnimeList", color=Color.blue()))
            maluser.fetch_manga_list()

            await message.edit(embed=Embed(title="Fetching manga chapters from Nelomanga", color=Color.blue()))
            maluser.fetch_manga_chapters()
        except error.UserNotFound:
            await message.edit(embed=Embed(title="MyAnimeList user wasn't found", color=Color.dark_orange()))
            return

        VolatileStorage[f"mal.user.{user_id}"] = maluser

        # save new user, in case that notify_user crashes the bot
        maluser.save_to_storage()

        await message.edit(embed=Embed(title="Successfully registered for new release notifications",
                                       color=Color.blue()))

        # force-update the user once after registration
        await self.notify_user(user_id, maluser)

    @util.discord.grouped_hybrid_command(
        name="deregister",
        description="Deregister the connected MyAnimeList account from your discord account",
        command_group=command_group
    )
    async def deregister(self, ctx: commands.context.Context | discordpy.interactions.Interaction):
        """The discord command 'niko.mal.dergister'"""

        user_id = util.discord.get_user_id(ctx)

        if not VolatileStorage.contains(f"mal.user.{user_id}"):
            await util.discord.reply(ctx,
                                     embed=Embed(title="You are not yet registered", color=Color.orange()))
            return

        del VolatileStorage[f"mal.user.{user_id}"]
        del PersistentStorage[f"mal.user.{user_id}"]

        await util.discord.reply(ctx,
                                 embed=Embed(title="Successfully deregistered from release notifications",
                                             color=Color.blue()))

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

        if not VolatileStorage.contains(f"mal.user.{user_id}"):
            await util.discord.reply(ctx,
                                     embed=Embed(title="You are not yet registered", color=Color.orange()))
            return

        embed = Embed(title="Checking for new chapters...",
                      description="Please wait a few minutes",
                      color=Color.blue())
        message = await util.discord.reply(ctx, embed=embed)

        maluser = VolatileStorage[f"mal.user.{user_id}"]
        await self.notify_user(int(user_id), maluser)

        await message.edit(embed=Embed(title="Finished checking!", color=Color.blue()))

    @util.discord.grouped_hybrid_command(
        name="updateall",
        description="Check for new manga chapters for the MyAnimeList account connected to your discord account",
        command_group=command_group
    )
    @commands.is_owner()
    async def updateall(self, ctx: commands.context.Context | discordpy.interactions.Interaction):
        """The discord command 'niko.mal.updateall'"""

        embed = Embed(title="Checking for new chapters...",
                      description="Please wait a few minutes",
                      color=Color.blue())
        message = await util.discord.reply(ctx, embed=embed)

        for user_id, maluser in VolatileStorage["mal.user"].items():
            await self.notify_user(int(user_id), maluser)

        await message.edit(embed=Embed(title="Finished checking!", color=Color.blue()))

    @tasks.loop(hours=1, reconnect=True, name="notify-users-task")
    async def notify_users(self):
        """A method responsible for notifying users if a new manga chapter was released"""

        if not VolatileStorage.contains("mal.user"):
            return

        try:
            for user_id, maluser in VolatileStorage["mal.user"].items():
                if not isinstance(user_id, str): raise TypeError()
                if not isinstance(maluser, MALUser): raise TypeError()

                await self.notify_user(int(user_id), maluser)

                # avoid rate limits
                await sleep(60)
        except requests.exceptions.ConnectionError as exc:
            if "NameResolutionError" in str(exc):
                try:
                    requests.get("https://google.com", timeout=5)
                except:
                    logger.error("NameResolutionError while fetching new chapters: DNS server not reachable")
                    return

                logger.error(f"NameResolutionError while fetching new chapters: {exc}")
                return

            logger.error(f"ConnectionError while fetching new chapters: {exc}")
            return

    async def notify_user(self, user_id: int, maluser: MALUser) -> None:
        """Notify the user if any of his ``Manga`` got a new chapter"""

        if not isinstance(user_id, int): raise TypeError()
        if not isinstance(maluser, MALUser): raise TypeError()

        maluser.fetch_manga_list()

        for manga in maluser.manga.values():
            if not isinstance(manga, Manga): raise TypeError()

            if manga._time_next_notify < datetime.now():
                await self.notify_manga(user_id, manga)

                # avoid rate limits
                await sleep(5)

        maluser.save_to_storage()

    async def notify_manga(self, user_id: int, manga: Manga) -> None:
        """Notify the user if the given ``Manga`` received a new chapter"""

        if not isinstance(user_id, int): raise TypeError()
        if not isinstance(manga, Manga): raise TypeError()

        if not manga.fetch_chapters():
            manga._time_next_notify = datetime.now() + timedelta(days=7)
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

    async def get_manga(self,
                        input_data: str,
                        user_id: int,
                        ctx: commands.context.Context | discordpy.interactions.Interaction | None = None) \
       -> Manga | None:
        """Helper function to process user input and fetch the requested manga"""

        if input_data.isdecimal():
            mal_id = int(input_data)
        else:
            mal_id = mal_helper.search_for_manga(input_data)
            if mal_id is None:
                if ctx is not None:
                    embed = Embed(title="Manga not found on MyAnimeList", color=Color.orange())
                    await util.discord.reply(ctx, embed=embed)
                else:
                    logger.warning(f"Manga {input_data} not found on MyAnimeList")
                return None

        manga = None

        if VolatileStorage.contains(f"mal.user.{user_id}"):
            maluser: MALUser = VolatileStorage[f"mal.user.{user_id}"]

            maluser.fetch_manga_list()

            if mal_id in maluser.manga:
                manga = maluser.manga[mal_id]

                manga.fetch_chapters()

        if manga is None:
            try:
                manga = Manga.from_mal_id(mal_id)
            except error.MediaTypeError:
                if ctx is not None:
                    embed = Embed(title="Currently only supports manga and not light novel/novel",
                                  color=Color.orange())
                    await util.discord.reply(ctx, embed=embed)
                else:
                    logger.warning("Currently only supports manga and not light novel/novel")
                return None

        return manga

    def import_users(self):
        """Import all MALUsers from ``abllib.PersistentStorage``"""

        if PersistentStorage.contains("mal.user"):
            for user_id, maluser_json in PersistentStorage["mal.user"].items():
                try:
                    maluser = MALUser.from_export(int(user_id), maluser_json)
                    util.general.sync(self.notify_user(int(user_id), maluser))
                    VolatileStorage[f"mal.user.{user_id}"] = maluser
                # pylint: disable-next=broad-exception-caught
                except Exception:
                    logger.exception(f"Failed to import MAL user {user_id}, error:")

        imported = len(VolatileStorage.get("mal.user", default=[]))
        total = len(PersistentStorage.get("mal.user", default=[]))
        logger.info(f"Finished importing {imported}/{total} MAL user(s)")

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    mal_helper._setup()
    manganato_helper._setup()
    natomanga_helper._setup()

    cog = MALNotifier(bot)

    cog.notify_users.start()

    Thread(target=cog.import_users, daemon=True).start()

    await bot.add_cog(cog)

# pylint: enable=protected-access
