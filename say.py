import discord
from discord.ext import commands
from gtts import gTTS
import os
import asyncio
from flask import Flask
from threading import Thread
import time
import datetime

# --- THÊM 2 DÒNG NÀY ĐỂ FIX LỖI FFMEG TRÊN RENDER ---
try:
    from static_ffmpeg import add_paths
    add_paths()
except ImportError:
    print("static_ffmpeg not available, proceeding without it.")

# --- BIẾN TOÀN CỤC ĐỂ THEO DÕI UPTIME ---
start_time = datetime.datetime.now()

# --- CẤU HÌNH WEB SERVER ĐỂ TREO 24/7 ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CẤU HÌNH DISCORD BOT ---
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def create_tts(text):
    filename = f"voice_{int(time.time())}.mp3"
    tts = gTTS(text=text, lang='vi')
    tts.save(filename)
    return filename

# --- CÁC LỆNH CỦA BOT ---

@bot.command()
async def say(ctx, *, message: str):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        vc = ctx.voice_client or await channel.connect()
        fname = create_tts(message)
        vc.play(discord.FFmpegPCMAudio(fname), after=lambda e: os.remove(fname))
    else:
        await ctx.send("Bạn cần vào một kênh voice trước!")

@bot.command()
async def uptime(ctx):
    now = datetime.datetime.now()
    delta = now - start_time
    
    # Tính toán Ngày, Giờ, Phút, Giây
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    
    uptime_msg = f"🚀 **Chị Google đã online được:** `{days} ngày, {hours} giờ, {minutes} phút, {seconds} giây`"
    await ctx.send(uptime_msg)

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
    # Nghỉ 5 giây để Flask ổn định trước khi login Discord (tránh lỗi 503 overflow)
    time.sleep(5)
    
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        print(f"[{datetime.datetime.now()}] Bot đang đăng nhập...")
        bot.run(token)
    else:
        print("LỖI: Không tìm thấy DISCORD_TOKEN trong cấu hình!")