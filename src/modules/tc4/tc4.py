"""contains the cog of the tc4 module"""

import os

from discord.ext import commands

from .aspect import Aspect
from .aspect_parser import AspectParser
from .shortest_path import ShortestPath
from .shortest_path2 import ShortestPath2

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
        
        self.sp2 = ShortestPath2(list(self.aspects.values()))
        self.sp2.calculate_graph()

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
        name="tc4.exactpath",
        brief="The cheapest path between two aspects considering cost",
        description="Return the chespest path between two aspects, also considering their cost.")
    async def exactpath(self, ctx: commands.context.Context, aspect_name_1: str, aspect_name_2):
        """The shortest path between two aspects"""

        aspect_objs = [self._find_aspect(aspect_name_1), self._find_aspect(aspect_name_2)]
        if aspect_objs[0] is None:
            await ctx.message.reply(f"The aspect {aspect_name_1} wasn't found!")
            return
        if aspect_objs[1] is None:
            await ctx.message.reply(f"The aspect {aspect_name_2} wasn't found!")
            return

        sp = ShortestPath(self.aspects).recursive(*aspect_objs)[0]
        to_send = [sp[0].embed()]
        path = str(sp[0])
        for aspect in sp[1::]:
            to_send.append(aspect.embed())
            path += f" -> {aspect}"
        await ctx.message.reply(path, embeds=([item[0] for item in to_send]),
                                files=([item[1] for item in to_send]))

    @commands.command(
        name="tc4.path",
        brief="The shortest path between two aspects",
        description="Return the shortest path between two aspects, not considering their cost.")
    async def path(self, ctx: commands.context.Context, aspect_name_1: str, aspect_name_2):
        """The shortest path between two aspects"""

        if ctx.author.name != "ableytner":
            await ctx.message.reply(f"The path command is currently broken, use exactpath instead!")

        aspect1 = self._find_aspect(aspect_name_1)
        aspect2 = self._find_aspect(aspect_name_2)

        if not aspect1:
            await ctx.message.reply(f"The aspect {aspect_name_1} wasn't found!")
            return
        if not aspect2:
            await ctx.message.reply(f"The aspect {aspect_name_2} wasn't found!")
            return

        aspect_objs = [self.sp2.all_nodes[aspect1.name], self.sp2.all_nodes[aspect2.name]]

        sp = self.sp2.recursive(*aspect_objs)
        to_send = [sp[0].embed()]
        path = str(sp[0])
        for aspect in sp[1::]:
            to_send.append(aspect.embed())
            path += f" -> {aspect}"
        await ctx.message.reply(path, embeds=([item[0] for item in to_send]),
                                files=([item[1] for item in to_send]))

    def _find_aspect(self, aspect_name: str) -> Aspect | None:
        aspect_name = aspect_name.capitalize()
        aspect_obj = None

        if aspect_name in self.aspects.keys():
            aspect_obj = self.aspects[aspect_name]

        for aspect in self.aspects.values():
            if aspect.keyword == aspect_name.lower():
                aspect_obj = aspect

        return aspect_obj

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(TC4(bot))
