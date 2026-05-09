import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio
import time
from static_ffmpeg import add_paths
add_paths()

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Hàm tạo file âm thanh (copy từ logic Music sang để dùng nội bộ)
    def create_tts(self, text):
        fname = f"welcome_{int(time.time())}.mp3"
        tts = gTTS(text=text, lang='vi')
        tts.save(fname)
        return fname

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # 1. Không tự chào chính mình (bot)
        if member.id == self.bot.user.id:
            return

        # 2. Kiểm tra nếu người dùng vừa tham gia vào một kênh voice (sau khi đổi kênh hoặc mới vào)
        if after.channel is not None and (before.channel is None or before.channel.id != after.channel.id):
            channel = after.channel
            # Tìm xem bot đã có trong voice của server này chưa
            vc = discord.utils.get(self.bot.voice_clients, guild=member.guild)
            
            try:
                # 3. Logic kết nối hoặc chuyển kênh
                if vc is None:
                    # Nếu bot chưa ở trong kênh nào, kết nối mới
                    vc = await channel.connect()
                elif vc.channel.id != channel.id:
                    # Nếu bot đang ở kênh khác, bay sang kênh mới cùng user
                    await vc.move_to(channel)

                # Đợi 1 giây cho kết nối ổn định rồi mới nói
                await asyncio.sleep(1)
                
                # 4. Tạo câu chào cá nhân hóa
                welcome_text = f"Chào mừng {member.display_name} đã tham gia"
                fname = self.create_tts(welcome_text)
                
                # 5. Phát âm thanh (chỉ phát nếu không bận nói gì khác)
                if not vc.is_playing():
                    vc.play(discord.FFmpegPCMAudio(fname), after=lambda e: os.remove(fname))
                else:
                    # Nếu đang bận thì xóa file ngay để tránh rác server
                    os.remove(fname)

                print(f"[{time.strftime('%H:%M:%S')}] Đã chào: {member.display_name} tại {channel.name}")

            except Exception as e:
                print(f"Lỗi Voice Event: {e}")

async def setup(bot):
    await bot.add_cog(Events(bot))