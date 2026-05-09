import discord
from discord.ext import commands
from gtts import gTTS
import os
import time
from static_ffmpeg import add_paths
add_paths()

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_tts(self, text):
        fname = f"v_{int(time.time())}.mp3"
        gTTS(text=text, lang='vi').save(fname)
        return fname

    @commands.command()
    async def say(self, ctx, *, msg: str):
        if ctx.author.voice:
            vc = ctx.voice_client or await ctx.author.voice.channel.connect()
            fname = self.create_tts(msg)
            vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=fname), after=lambda e: os.remove(fname))
        else:
            await ctx.send(f"Vào voice đi {ctx.author.display_name} ơi!")

async def setup(bot):
    await bot.add_cog(Music(bot))