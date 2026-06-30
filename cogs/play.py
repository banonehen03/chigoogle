import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
from PIL import Image, ImageDraw
from io import BytesIO

# Cấu hình yt-dlp tối ưu riêng cho SoundCloud
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'scsearch', # Ép hệ thống tìm kiếm trên SoundCloud
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

    # Hàm vẽ ảnh danh sách bài hát (Menu từ 1 đến 5) bằng Pillow
    def create_menu_image(self, tracks):
        img_h = (len(tracks) * 60) + 60
        image = Image.new("RGBA", (500, img_h), (40, 40, 40, 255))
        draw = ImageDraw.Draw(image)
        
        # Tiêu đề màu xanh neon rực rỡ
        draw.text((20, 15), "DANH SÁCH BÀI HÁT SOUNDCLOUD", fill=(255, 102, 0, 255))
        
        y_offset = 50
        for i, track in enumerate(tracks):
            # Vẽ số thứ tự
            draw.text((20, y_offset + 15), f"{i+1}.", fill=(255, 255, 255, 255))
            
            # Vẽ tên bài hát (cắt ngắn nếu quá dài)
            title = track.get('title', 'Unknown Title')
            if len(title) > 40: title = title[:37] + "..."
            draw.text((50, y_offset + 5), title, fill=(255, 215, 0, 255))
            
            # Vẽ thông tin nghệ sĩ/thời lượng
            duration = track.get('duration_string', 'N/A')
            uploader = track.get('uploader', 'SoundCloud Artist')
            draw.text((50, y_offset + 25), f"🎵 Artist: {uploader} | ⏱️ {duration}", fill=(180, 180, 180, 255))
            
            # Đường gạch ngang phân cách
            draw.line([(20, y_offset + 50), (480, y_offset + 50)], fill=(60, 60, 60, 255))
            y_offset += 60
            
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    @commands.command(name="play")
    async def search(self, ctx, *, query: str):
        """Tìm kiếm nhạc trên SoundCloud và trả về menu ảnh"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Việt ơi, bạn phải vào một phòng thoại (Voice Channel) trước đã nha!")
            return

        await ctx.send(f"🔍 Đang tìm kiếm trên SoundCloud: **{query}**...")

        # Sử dụng yt-dlp quét kết quả từ SoundCloud trực tiếp
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            try:
                # Tìm kiếm lấy ra 5 kết quả hàng đầu
                info = ydl.extract_info(f"scsearch5:{query}", download=False)
                if 'entries' not in info or not info['entries']:
                    await ctx.send("❌ Không tìm thấy bài hát nào trên SoundCloud phù hợp rồi Việt ơi.")
                    return
                
                tracks = info['entries']
                self.search_results[ctx.author.id] = tracks # Lưu tạm vào bộ nhớ user
                
                # Vẽ menu ảnh bằng Pillow
                menu_buffer = self.create_menu_image(tracks)
                discord_file = discord.File(fp=menu_buffer, filename="sc_music_menu.png")
                
                await ctx.send(content="👉 **Nhập số (1, 2, 3, 4, 5) để chọn bài hát phát vào Voice:**", file=discord_file)

            except Exception as e:
                await ctx.send(f"❌ Lỗi khi tìm kiếm nhạc SoundCloud: {e}")

    # Lắng nghe sự kiện gõ số để chọn bài hát phát vào voice
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        author_id = message.author.id
        if author_id in self.search_results:
            content = message.content.strip()
            
            if content.isdigit():
                choice = int(content) - 1
                tracks = self.search_results[author_id]
                
                if 0 <= choice < len(tracks):
                    selected_track = tracks[choice]
                    del self.search_results[author_id] # Xóa khỏi hàng chờ ngay sau khi chọn
                    
                    ctx = await self.bot.get_context(message)
                    await self.play_audio(ctx, selected_track)

    async def play_audio(self, ctx, track):
        voice_channel = ctx.author.voice.channel
        await ctx.send(f"⏳ Đang lấy luồng audio stream SoundCloud cho bài: **{track.get('title')}**...")
        
        try:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc:
                if vc.channel != voice_channel: 
                    await vc.move_to(voice_channel)
            else:
                vc = await voice_channel.connect()

            if vc.is_playing(): 
                vc.stop()

            # Lấy link stream thực tế (SoundCloud mượt mà không bao giờ chặn IP)
            stream_url = track['url']

            await ctx.send(f"🧡 **Đang phát (SoundCloud):** **{track.get('title')}** tại phòng `{voice_channel.name}`")
            vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=stream_url, **FFMPEG_OPTIONS))
            
        except Exception as e:
            await ctx.send(f"❌ Lỗi khi phát nhạc SoundCloud: {e}")

async def setup(bot):
    await bot.add_cog(MusicBot(bot))