import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.id == self.bot.user.id: return
        if after.channel and (not before.channel or before.channel.id != after.channel.id):
            vc = discord.utils.get(self.bot.voice_clients, guild=member.guild)
            if not vc: vc = await after.channel.connect()
            # Thêm logic tạo TTS và phát tại đây tương tự file cũ
            print(f"{member.name} joined.")

async def setup(bot):
    await bot.add_cog(Events(bot))