import static_ffmpeg
static_ffmpeg.add_paths()
import discord
from discord.ext import commands
import os
import asyncio
from flask import Flask
from threading import Thread
import time

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is alive!"

def run():
    import logging
    # Tắt hoàn toàn các log thừa để tránh xung đột và nặng máy
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    port = int(os.environ.get("PORT", 8080))
    # Thêm tham số threaded=True để xử lý nhiều yêu cầu cùng lúc
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, threaded=True)

def keep_alive():
    Thread(target=run).start()

# --- DISCORD BOT ---
intents = discord.Intents.default()
intents.members = True 
intents.message_content = True
intents.voice_states = True

# Thêm help_command=None vào đây để tắt cái bảng đen mặc định
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with bot:
        keep_alive()
        await load_extensions()
        token = os.environ.get('DISCORD_TOKEN')
        await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())