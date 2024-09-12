from datetime import datetime, timedelta
from threading import Thread

import discord
from discord import app_commands
from discord.ext import commands, tasks

from . import manganato_helper, mal_helper, exec
from .mal_user import MALUser
from .manga import Manga
from ... import util

with open("client_id.txt", "r", encoding="utf8") as file:
    CLIENT_ID = file.readlines()[0]

command_group = app_commands.Group(
    name="mal",
    description="The module for MyAnimeList-related commands"
)

class MALNotifier(commands.Cog):
    "The module for MyAnimeList-related commands"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.users = []

    @util.discord.normal_command(
        name="search",
        description="",
        hidden=True
    )
    @commands.is_owner()
    async def search(self, ctx: commands.context.Context, *manga_name: list[str]):
        recombined_name = " ".join(["".join(item) for item in manga_name])
        manga_url = manganato_helper.get_manga_url(" ".join(recombined_name))
        chapters = manganato_helper.get_chapters(manga_url)
        latest_chap = manganato_helper.get_latest_chapter(chapters)

        print(len(chapters))
        print(latest_chap.number)

        await util.discord.reply(ctx, manga_url)

    @util.discord.normal_command(
        name="search2",
        description="",
        hidden=True
    )
    @commands.is_owner()
    async def search2(self, ctx: commands.context.Context, mal_id: int):
        try:
            manga = Manga.from_mal_id(mal_id)
        except exec.MangaNotFound:
            await util.discord.reply(ctx, "Manga not found on MAL")
            return
        except exec.MediaTypeError:
            await util.discord.reply(ctx, "Currently only supports manga and not light novel/novel")
            return

        embed, file = manga.to_embed()
        await util.discord.reply(ctx, embed=embed, file=file)

    @util.discord.grouped_hybrid_command(
        name="register",
        description="register an existing MyAnimeList account for use with the discord bot",
        command_group=command_group
    )
    async def register(self, ctx: commands.context.Context | discord.interactions.Interaction, username: str):
        if util.discord.is_slash_command(ctx):
            user_id = ctx.user.id
        else:
            user_id = ctx.author.id

        if util.VolatileStorage.contains(f"mal.user", str(user_id)):
            await util.discord.reply(ctx, embed=discord.Embed(title="You are already registered", color=discord.Color.orange()))
            return

        message = await util.discord.reply(ctx, embed=discord.Embed(title="Fetching manga list from MyAnimeList", color=discord.Color.blue()))

        try:
            maluser = MALUser(username.lower(), user_id)
            await message.edit(embed=discord.Embed(title="Fetching manga list from MyAnimeList", color=discord.Color.blue()))
            maluser.fetch_manga_list()
            await message.edit(embed=discord.Embed(title="Fetching manga chapters from Manganato", color=discord.Color.blue()))
            maluser.fetch_manga_chapters()
        except exec.UserNotFound:
            await message.edit(embed=discord.Embed(title="MyAnimeList user wasn't found", color=discord.Color.dark_orange()))
            return

        util.VolatileStorage[f"mal.user.{user_id}"] = maluser
        await message.edit(embed=discord.Embed(title="Successfully registered for new release notifications", color=discord.Color.blue()))

    @util.discord.grouped_hybrid_command(
        name="deregister",
        description="deregister the connected MyAnimeList account from your discord account",
        command_group=command_group
    )
    async def deregister(self, ctx: commands.context.Context | discord.interactions.Interaction):
        if util.discord.is_slash_command(ctx):
            user_id = ctx.user.id
        else:
            user_id = ctx.author.id

        if not util.VolatileStorage.contains(f"mal.user", str(user_id)):
            await util.discord.reply(ctx, embed=discord.Embed(title="You are not yet registered", color=discord.Color.orange()))
            return

        del util.VolatileStorage[f"mal.user.{user_id}"]
        await util.discord.reply(ctx, embed=discord.Embed(title="Successfully deregistered from release notifications", color=discord.Color.blue()))

    @tasks.loop(hours=1, reconnect=True, name="notify-users-task")
    async def notify_users(self):
        if not util.VolatileStorage.exists("mal.user"):
            return

        for user_id, maluser in util.VolatileStorage["mal.user"].items():
            if not isinstance(user_id, str): raise TypeError()
            if not isinstance(maluser, MALUser): raise TypeError()

            maluser.fetch_manga_list()

            for manga in maluser.manga.values():
                if not isinstance(manga, Manga): raise TypeError()

                if manga._time_next_notify < datetime.now():
                    await self._handle_manga(int(user_id), manga)

    async def _handle_manga(self, user_id: int, manga: Manga) -> None:
        manga.fetch_chapters()
        if manga._chapters_total > manga._chapters_read \
            and manga._chapters_total > manga._chapters_last_notified:
            embed, file = manga.to_embed()

            new_chapters = manga._chapters_total - manga._chapters_read
            if new_chapters == 1:
                embed.title += "  |  1 new chapter"
            else:
                embed.title += f"  |  {new_chapters} new chapters"

            await util.discord.private_message(user_id, embed=embed, file=file)

            manga._chapters_last_notified = manga._chapters_total
            manga._time_next_notify = datetime.now() + timedelta(hours=1)

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    util.VolatileStorage["mal.CLIENT-ID"] = CLIENT_ID

    mal_helper._setup()
    manganato_helper._setup()

    if util.PersistentStorage.exists("mal.user"):
        def import_users():
            c = 0
            for user_id, maluser_json in util.PersistentStorage["mal.user"].items():
                maluser = MALUser.from_export(int(user_id), maluser_json)
                maluser.fetch_manga_chapters()
                util.VolatileStorage[f"mal.user.{user_id}"] = maluser
                c += 1
            print(f"Finished importing {c} MAL user(s)")

        Thread(target=import_users, daemon=True).start()

    cog = MALNotifier(bot)

    cog.notify_users.start()

    await bot.add_cog(cog)
