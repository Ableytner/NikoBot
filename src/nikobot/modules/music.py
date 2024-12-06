# pylint: skip-file

import logging

import discord as discordpy
import youtube_dl
from discord.ext import commands, tasks

logger = logging.getLogger("music")

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.emojis = {"pause": "⏸️", "resume": "▶️", "skip": "⏭️", "stop": "❌"}
        self.active_plays = {}

        self.song_scheduler.start()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discordpy.reaction.Reaction, user: discordpy.member.Member):
        if reaction.message.id not in self.active_plays.keys():
            return


    @commands.command()
    async def come(self, ctx: commands.context.Context):
        """Join the users voice channel if it isn't None"""

        if ctx.author.voice is None:
            await ctx.channel.send("You aren't connected to a voice channel!")
            return

        new_voice_channel = ctx.author.voice.channel

        if ctx.voice_client is None:
            logger.debug(f"Joining channel: {new_voice_channel.name}")
            await new_voice_channel.connect()
        elif ctx.voice_client.channel.id != new_voice_channel.id:
            logger.debug(f"Moving to channel: {new_voice_channel.name}")
            await ctx.voice_client.move_to(new_voice_channel)

    @commands.command()
    async def go(self, ctx: commands.context.Context):
        """Leave the voice channel"""

        if ctx.voice_client != None:
            await ctx.voice_client.disconnect()

    @commands.command()
    async def sing(self, ctx: commands.context.Context, url: str):
        """Add a song to the queue"""

        await self.come(ctx)

        if ctx.guild.id in self.active_plays.keys():
            self.active_plays[ctx.guild.id]["urls"].append(url)
            await ctx.channel.send("Song added to queue")
            return

        playback_msg = await ctx.send(f"Now playing ")
        await playback_msg.add_reaction(self.emojis["pause"])
        await playback_msg.add_reaction(self.emojis["resume"])
        await playback_msg.add_reaction(self.emojis["skip"])
        await playback_msg.add_reaction(self.emojis["stop"])

        data = {
            "message_id": playback_msg.id,
            "vc_id": ctx.author.voice.channel.id,
            "urls": [url],
            "playing": False,
            "paused": False
        }
        self.active_plays[ctx.guild.id] = data

    @commands.command()
    async def pause(self, ctx: commands.context.Context):
        """Pause playback"""

        ctx.voice_client.pause()
        self.active_plays[ctx.guild.id]["paused"] = True
        await ctx.channel.send("paused playback")

    @commands.command()
    async def resume(self, ctx: commands.context.Context):
        """Resume playback"""

        ctx.voice_client.resume()
        self.active_plays[ctx.guild.id]["paused"] = False
        await ctx.channel.send("resumed playback")

    @commands.command()
    async def skip(self, ctx: commands.context.Context):
        """Skip the current song"""

        ctx.voice_client.stop()
        await ctx.channel.send("skipped song")

    @commands.command()
    async def stop (self, ctx: commands.context.Context):
        """Stop playback"""

        self.active_plays[ctx.guild.id]["urls"].clear()
        ctx.voice_client.stop()
        await ctx.channel.send("stopped playback")

    @tasks.loop(seconds=5)
    async def song_scheduler(self):
        """manages the queue"""

        # list() to create a new object which can't change during the loop execution
        for guild_id in list(self.active_plays.keys()):
            data = self.active_plays[guild_id]

            if not data["playing"] and len(data["urls"]) > 0:
                data["playing"] = True
                url = data["urls"].pop(0)

                logger.debug("Playing next song...")
                await self.play_song(url, guild_id)

    async def play_song(self, url: str, guild_id: int):
        """ plays back the given song """

        FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn"
        }
        YDL_OPTIONS = {
            "format" : "bestaudio"
        }

        voice_clients: list[discordpy.voice_client.VoiceClient] = self.bot.voice_clients
        vc: discordpy.voice_client.VoiceClient = [item for item in voice_clients if item.guild.id==guild_id][0]
        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download = False)
            url2 = info["formats"][0]["url"]
            source = await discordpy.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
            vc.play(source, after=lambda *x:self.song_finished(guild_id))

    def song_finished(self, guild_id: int):
        """callback for when a song finishes playing"""

        self.active_plays[guild_id]["playing"] = False
        logger.debug("Song finished")

async def setup(bot: commands.Bot):
    """Setup the bot_commands cog"""

    await bot.add_cog(Music(bot))
