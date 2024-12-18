"""contains the cog of the tc4 module"""

import logging
import os
from threading import Thread

from discord import app_commands
from discord.ext import commands

from .aspect import Aspect
from .aspect_parser import AspectParser
from .shortest_path3 import Graph
from ... import util

PATH = __file__.rsplit(os.sep, maxsplit=1)[0]

logger = logging.getLogger("tc4")

command_group = app_commands.Group(
    name="tc4",
    description="The module for Thaumcraft 4-related commands"
)

class TC4(commands.Cog):
    """The module for Thaumcraft 4-related commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        parser = AspectParser(f"{PATH}/aspects.txt")
        self.aspects = parser.parse()

        for aspect in self.aspects.values():
            aspect.construct_neighbors(self.aspects)
            if not os.path.isfile(f"{PATH}/assets/{aspect.name.lower()}.png"):
                logger.error(f"Icon for aspect {aspect.name} not found!")

        self.graph = Graph(list(self.aspects.values()))

    @util.discord.grouped_hybrid_command(
        "aspect",
        "Prints out information about an Thaumcraft 4 aspect.",
        command_group
    )
    async def aspect(self, ctx: commands.context.Context, aspect_name: str):
        """Information about an aspect"""

        aspect_obj = self._find_aspect(aspect_name)
        if aspect_obj is None:
            await util.discord.reply(ctx, "That aspect wasn't found!")
            return

        embed_var, file_var = aspect_obj.to_embed()
        await util.discord.reply(ctx, embed=embed_var, file=file_var)

    @util.discord.grouped_hybrid_command(
        "path",
        "Return the cheapest path between two aspects, also considering their cost.",
        command_group
    )
    async def path(self, ctx: commands.context.Context, aspect_name_1: str, aspect_name_2: str):
        """The shortest path between two aspects"""

        logger.info(f"Calculating path between {aspect_name_1} and {aspect_name_2}")

        aspect_objs = [self._find_aspect(aspect_name_1), self._find_aspect(aspect_name_2)]
        if aspect_objs[0] is None:
            await util.discord.reply(ctx, f"The aspect {aspect_name_1} wasn't found!")
            return
        if aspect_objs[1] is None:
            await util.discord.reply(ctx, f"The aspect {aspect_name_2} wasn't found!")
            return

        sp = self.graph.calc_shortest_path(*[item.name for item in aspect_objs])

        to_send = [sp[0].to_embed()]
        path = str(sp[0])
        for aspect in sp[1::]:
            to_send.append(aspect.to_embed())
            path += f" -> {aspect}"
        await util.discord.reply(ctx,
                                 path,
                                 embeds=([item[0] for item in to_send]),
                                 files=([item[1] for item in to_send]))

    def _find_aspect(self, aspect_name: str) -> Aspect | None:
        aspect_name = aspect_name.capitalize()

        if aspect_name in self.aspects:
            return self.aspects[aspect_name]

        for aspect in self.aspects.values():
            if aspect.keyword == aspect_name.lower():
                return aspect

        return None

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    cog = TC4(bot)

    Thread(target=cog.graph.construct, daemon=True).start()

    await bot.add_cog(cog)
