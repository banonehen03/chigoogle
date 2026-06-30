import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Cấu hình yt-dlp chỉ để STREAM nhạc từ Link (Không dùng để search nữa nên không lo bị chặn bot)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'source_address': '0.0.0.0',
    'nocheckcertificate': True
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.search_results = {}

    def create_menu_image(self, tracks):
        img_h = (len(tracks) * 60) + 60
        image = Image.new("RGBA", (500, img_h), (40, 40, 40, 255))
        draw = ImageDraw.Draw(image)
        
        draw.text((20, 15), "DANH SÁCH BÀI HÁT TÌM THẤY", fill=(0, 255, 128, 255))
        
        y_offset = 50
        for i, track in enumerate(tracks):
            draw.text((20, y_offset + 15), f"{i+1}.", fill=(255, 255, 255, 255))
            
            title = track['title']
            if len(title) > 40: title = title[:37] + "..."
            draw.text((50, y_offset + 5), title, fill=(255, 215, 0, 255))
            draw.text((50, y_offset + 25), f"📺 Nguồn: YouTube | Channel: {track.get('uploader', 'Ẩn')}", fill=(180, 180, 180, 255))
            
            draw.line([(20, y_offset + 50), (480, y_offset + 50)], fill=(60, 60, 60, 255))
            y_offset += 60
            
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    # Hàm tìm kiếm bằng YouTube API chính thống (Không bao giờ dính lỗi Sign in)
    def search_youtube_api(self, query, api_key):
        url = "https://www.googleapis.com/customsearch/v1"
        # Tận dụng Custom Search Engine của Việt để cào kết quả từ youtube.com
        params = {
            'q': f"site:youtube.com/watch {query}",
            'cx': os.environ.get('SEARCH_ENGINE_ID'),
            'key': api_key,
            'num': 5
        }
        try:
            res = requests.get(url, params=params).json()
            tracks = []
            if "items" in res:
                for item in res["items"]:
                    link = item.get("link")
                    if "watch?v=" in link:
                        tracks.append({
                            'title': item.get('title').replace(" - YouTube", ""),
                            'url': link,
                            'uploader': item.get('displayLink', 'YouTube')
                        })
                return tracks
        except Exception:
            return []
        return []

    @commands.command(name="play")
    async def search(self, ctx, *, query: str):
        """Tìm kiếm nhạc chuẩn xác qua API sạch lỗi"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Việt ơi, vào Voice channel trước đã nha.")
            return

        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            await ctx.send("❌ Thiếu cấu hình GOOGLE_API_KEY trên Render rồi Việt ơi!")
            return

        await ctx.send(f"🔍 Đang dùng Google API lùng bài hát: **{query}**...")

        # Gọi hàm search qua API sạch
        tracks = self.search_youtube_api(query, api_key)

        if not tracks:
            await ctx.send("❌ Không tìm thấy bài hát nào qua API rồi Việt ơi.")
            return

        self.search_results[ctx.author.id] = tracks
        
        # Vẽ ảnh Pillow trả về menu
        menu_buffer = self.create_menu_image(tracks)
        discord_file = discord.File(fp=menu_buffer, filename="music_menu.png")
        
        await ctx.send(content="👉 **Nhập số (1, 2, 3, 4, 5) để chọn bài hát phát vào Voice:**", file=discord_file)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        author_id = message.author.id
        
        if author_id in self.search_results:
            content = message.content.strip()
            if content.isdigit():
                choice = int(content) - 1
                tracks = self.search_results[author_id]
                
                if 0 <= choice < len(tracks):
                    selected_track = tracks[choice]
                    del self.search_results[author_id]
                    
                    ctx = await self.bot.get_context(message)
                    await self.play_audio(ctx, selected_track)

    async def play_audio(self, ctx, track):
        voice_channel = ctx.author.voice.channel
        await ctx.send(f"⏳ Đang lấy luồng audio trực tiếp cho bài: **{track['title']}**...")
        
        try:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc:
                if vc.channel != voice_channel: await vc.move_to(voice_channel)
            else:
                vc = await voice_channel.connect()

            if vc.is_playing(): vc.stop()

            # Bốc luồng stream thực tế từ Link bằng yt-dlp (chỉ xử lý link cụ thể nên qua mặt được bot detection)
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(track['url'], download=False)
                stream_url = info['url']

            await ctx.send(f"🎶 Đang phát: **{track['title']}**")
            vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=stream_url, **FFMPEG_OPTIONS))
            
        except Exception as e:
            await ctx.send(f"❌ Lỗi khi bốc luồng phát nhạc: {e}")

async def setup(bot):
    await bot.add_cog(MusicBot(bot))