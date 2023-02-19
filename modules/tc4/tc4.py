import os

from discord.ext import commands

from .aspect import Aspect
from .aspect_parser import AspectParser
from .shortest_path import ShortestPath

class TC4(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        parser = AspectParser("modules/tc4/aspects.txt")
        self.aspects = parser.parse()
        for aspect in self.aspects.values():
            aspect.construct_neighbors(self.aspects)
            if not os.path.isfile(f"modules/tc4/assets/{aspect.name.lower()}.png"):
                print(f"Icon for aspect {aspect.name} not found!")

    @commands.command(name="tc4.aspect")
    async def aspect(self, ctx: commands.context.Context, aspect_name: str):
        aspect_obj = self._find_aspect(aspect_name)
        if aspect_obj is None:
            await ctx.message.reply("That aspect wasn't found!")
            return

        embed_var, file_var = aspect_obj.embed()
        await ctx.message.reply(embed=embed_var, file=file_var)

    @commands.command(name="tc4.path")
    async def path(self, ctx: commands.context.Context, aspect_name_1: str, aspect_name_2):
        aspect_objs = [self._find_aspect(aspect_name_1), self._find_aspect(aspect_name_2)]
        if aspect_objs[0] is None:
            await ctx.message.reply(f"The aspect {aspect_name_1} wasn't found!")
            return
        if aspect_objs[1] is None:
            await ctx.message.reply(f"The aspect {aspect_name_2} wasn't found!")
            return
        
        sp = ShortestPath(self.aspects).recursive(*aspect_objs)
        to_send = [sp[0].embed()]
        path = str(sp[0])
        for aspect in sp[1::]:
            to_send.append(aspect.embed())
            path += f" -> {aspect}"
        await ctx.message.reply(path, embeds=([item[0] for item in to_send]), files=([item[1] for item in to_send]))

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
