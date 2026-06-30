import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Cấu hình yt-dlp chỉ để STREAM luồng nhạc từ Link cụ thể (Không dùng để search)
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
        self.search_results = {} # Lưu tạm kết quả tìm kiếm theo từng user

    # Hàm vẽ ảnh danh sách bài hát (Menu từ 1 đến 5)
    def create_menu_image(self, tracks):
        img_h = (len(tracks) * 60) + 60
        image = Image.new("RGBA", (500, img_h), (40, 40, 40, 255))
        draw = ImageDraw.Draw(image)
        
        # Vẽ tiêu đề menu giống ảnh mẫu của Việt
        draw.text((20, 15), "DANH SÁCH BÀI HÁT TÌM THẤY", fill=(0, 255, 128, 255))
        
        y_offset = 50
        for i, track in enumerate(tracks):
            # Vẽ số thứ tự
            draw.text((20, y_offset + 15), f"{i+1}.", fill=(255, 255, 255, 255))
            
            # Vẽ tên bài hát (cắt ngắn nếu quá dài để không bị tràn ảnh)
            title = track['title']
            if len(title) > 40: title = title[:37] + "..."
            draw.text((50, y_offset + 5), title, fill=(255, 215, 0, 255))
            
            # Vẽ thông tin nguồn kênh
            draw.text((50, y_offset + 25), f"📺 Nguồn: YouTube | Kênh: {track.get('uploader', 'Ẩn')}", fill=(180, 180, 180, 255))
            
            # Vẽ đường gạch phân cách giữa các bài hát
            draw.line([(20, y_offset + 50), (480, y_offset + 50)], fill=(60, 60, 60, 255))
            y_offset += 60
            
        # Xuất ảnh ra bộ nhớ bytes để gửi trực tiếp lên Discord
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    # Hàm dùng API key chính thức để tìm kiếm (Không lo bị chặn)
    def search_youtube_api(self, query, api_key):
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'q': query,
            'part': 'snippet',
            'type': 'video',
            'maxResults': 5,
            'key': api_key
        }
        try:
            res = requests.get(url, params=params).json()
            tracks = []
            if "items" in res:
                for item in res["items"]:
                    video_id = item.get("id", {}).get("videoId")
                    snippet = item.get("snippet", {})
                    if video_id:
                        tracks.append({
                            'title': snippet.get('title'),
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'uploader': snippet.get('channelTitle', 'YouTube')
                        })
                return tracks
        except Exception as e:
            print(f"Lỗi hệ thống YouTube API: {e}")
            return []
        return []

    @commands.command(name="play")
    async def search(self, ctx, *, query: str):
        """Tìm kiếm nhạc bằng YouTube API chính chủ và trả về menu ảnh"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Việt ơi, bạn phải vào một phòng thoại (Voice Channel) trước đã nha!")
            return

        # Đọc biến môi trường YOUTUBE_API_KEY mà Việt vừa dán trên Render
        api_key = os.environ.get('YOUTUBE_API_KEY')
        if not api_key:
            await ctx.send("❌ Bot chưa đọc được biến `YOUTUBE_API_KEY` trên Render. Việt kiểm tra lại phần Environment nhé!")
            return

        await ctx.send(f"🔍 Đang dùng YouTube API tìm kiếm: **{query}**...")

        # Chạy hàm lấy danh sách bài hát qua API
        tracks = self.search_youtube_api(query, api_key)

        if not tracks:
            await ctx.send("❌ Không tìm thấy bài hát nào phù hợp qua API hoặc Key bị lỗi cấu hình.")
            return

        # Lưu kết quả tạm thời vào hàng đợi của user
        self.search_results[ctx.author.id] = tracks
        
        # Tự động vẽ ảnh menu bằng Pillow
        menu_buffer = self.create_menu_image(tracks)
        discord_file = discord.File(fp=menu_buffer, filename="music_menu.png")
        
        await ctx.send(content="👉 **Nhập số (1, 2, 3, 4, 5) để chọn bài hát phát vào Voice:**", file=discord_file)

    # Bộ lắng nghe bắt sự kiện gõ số chọn bài rảnh tay giống ảnh mẫu của Việt
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        author_id = message.author.id
        if author_id in self.search_results:
            content = message.content.strip()
            
            # Nếu Việt gõ số hợp lệ
            if content.isdigit():
                choice = int(content) - 1
                tracks = self.search_results[author_id]
                
                if 0 <= choice < len(tracks):
                    selected_track = tracks[choice]
                    del self.search_results[author_id] # Chọn xong thì xóa hàng đợi
                    
                    ctx = await self.bot.get_context(message)
                    await self.play_audio(ctx, selected_track)

    async def play_audio(self, ctx, track):
        voice_channel = ctx.author.voice.channel
        await ctx.send(f"⏳ Đang lấy luồng audio stream cho bài: **{track['title']}**...")
        
        try:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc:
                if vc.channel != voice_channel: 
                    await vc.move_to(voice_channel)
            else:
                vc = await voice_channel.connect()

            if vc.is_playing(): 
                vc.stop()

            # Trích xuất luồng audio trực tiếp từ link bằng yt-dlp
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(track['url'], download=False)
                stream_url = info['url']

            await ctx.send(f"🎶 Đang phát: **{track['title']}** tại phòng `{voice_channel.name}`")
            vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=stream_url, **FFMPEG_OPTIONS))
            
        except Exception as e:
            await ctx.send(f"❌ Lỗi khi phát nhạc vào phòng voice: {e}")

async def setup(bot):
    await bot.add_cog(MusicBot(bot))