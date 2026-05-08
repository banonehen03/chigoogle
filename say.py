import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio
from flask import Flask
from threading import Thread
import time

# --- CẤU HÌNH WEB SERVER ĐỂ TREO 24/7 ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    # Lấy PORT từ hệ thống Render cấp phát
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CẤU HÌNH DISCORD BOT ---
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Hàm tạo TTS với tên file duy nhất để tránh lỗi khi nhiều người dùng cùng lúc
def create_tts(text):
    filename = f"voice_{int(time.time())}.mp3"
    tts = gTTS(text=text, lang='vi')
    tts.save(filename)
    return filename

@bot.command()
async def say(ctx, *, message: str):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        vc = ctx.voice_client or await channel.connect()
        
        fname = create_tts(message)
        # Phát xong tự động xóa file để sạch bộ nhớ server
        vc.play(discord.FFmpegPCMAudio(fname), after=lambda e: os.remove(fname))
    else:
        await ctx.send("Bạn cần vào một kênh voice trước!")

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id:
        return

    if after.channel is not None and (before.channel is None or before.channel.id != after.channel.id):
        channel = after.channel
        vc = discord.utils.get(bot.voice_clients, guild=member.guild)
        
        try:
            if vc is None:
                vc = await channel.connect()
            elif vc.channel.id != channel.id:
                await vc.move_to(channel)

            await asyncio.sleep(1)
            
            welcome_text = f"Chào mừng {member.display_name} đã tham gia"
            fname = create_tts(welcome_text)
            
            if not vc.is_playing():
                vc.play(discord.FFmpegPCMAudio(fname), after=lambda e: os.remove(fname))
        except Exception as e:
            print(f"Lỗi Voice: {e}")

# --- KHỞI CHẠY ---
if __name__ == "__main__":
    keep_alive()
    # Đảm bảo bạn đã đặt DISCORD_TOKEN trong Environment Variables trên Render
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("LỖI: Không tìm thấy DISCORD_TOKEN trong cấu hình Render!")

