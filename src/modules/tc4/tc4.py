"""contains the cog of the tc4 module"""

import os

from discord.ext import commands

from .aspect import Aspect
from .aspect_parser import AspectParser
from .shortest_path3 import Graph

PATH = __file__.rsplit(os.sep, maxsplit=1)[0]

class TC4(commands.Cog):
    """The module for Thaumcraft 4-related commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        parser = AspectParser(f"{PATH}/aspects.txt")
        self.aspects = parser.parse()

        for aspect in self.aspects.values():
            aspect.construct_neighbors(self.aspects)
            if not os.path.isfile(f"{PATH}/assets/{aspect.name.lower()}.png"):
                print(f"Icon for aspect {aspect.name} not found!")

        self.graph = Graph(list(self.aspects.values()))
        self.graph.construct()

    @commands.command(
        name="tc4.aspect",
        brief="Information about an aspect",
        description="Prints out information about an Thaumcraft 4 aspect.")
    async def aspect(self, ctx: commands.context.Context, aspect_name: str):
        """Information about an aspect"""

        aspect_obj = self._find_aspect(aspect_name)
        if aspect_obj is None:
            await ctx.message.reply("That aspect wasn't found!")
            return

        embed_var, file_var = aspect_obj.embed()
        await ctx.message.reply(embed=embed_var, file=file_var)

    @commands.command(
        name="tc4.path",
        brief="The cheapest path between two aspects considering cost",
        description="Return the cheapest path between two aspects, also considering their cost.")
    async def path(self, ctx: commands.context.Context, aspect_name_1: str, aspect_name_2: str):
        """The shortest path between two aspects"""

        aspect_objs = [self._find_aspect(aspect_name_1), self._find_aspect(aspect_name_2)]
        if aspect_objs[0] is None:
            await ctx.message.reply(f"The aspect {aspect_name_1} wasn't found!")
            return
        if aspect_objs[1] is None:
            await ctx.message.reply(f"The aspect {aspect_name_2} wasn't found!")
            return
        
        sp = self.graph.calc_shortest_path(*[item.name for item in aspect_objs])

        to_send = [sp[0].embed()]
        path = str(sp[0])
        for aspect in sp[1::]:
            to_send.append(aspect.embed())
            path += f" -> {aspect}"
        await ctx.message.reply(path, embeds=([item[0] for item in to_send]),
                                files=([item[1] for item in to_send]))

    def _find_aspect(self, aspect_name: str) -> Aspect | None:
        aspect_name = aspect_name.capitalize()

        if aspect_name in self.aspects.keys():
            return self.aspects[aspect_name]

        for aspect in self.aspects.values():
            if aspect.keyword == aspect_name.lower():
                return aspect

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(TC4(bot))
