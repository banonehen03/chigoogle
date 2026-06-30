import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Cấu hình yt-dlp để lấy luồng audio từ YTB/SCL nhanh nhất
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.search_results = {} # Lưu tạm kết quả tìm kiếm theo từng user

    # Hàm vẽ menu danh sách bài hát bằng Pillow giống ảnh mẫu
    def create_menu_image(self, tracks):
        # Tạo một ảnh nền tối (Width: 600, Height: 50 * số bài + 40)
        img_h = (len(tracks) * 60) + 60
        image = Image.new("RGBA", (500, img_h), (40, 40, 40, 255))
        draw = ImageDraw.Draw(image)
        
        # Vẽ tiêu đề
        draw.text((20, 15), "DANH SÁCH BÀI HÁT TÌM THẤY", fill=(0, 255, 128, 255))
        
        y_offset = 50
        for i, track in enumerate(tracks):
            # Vẽ số thứ tự tròn hoặc viền
            draw.text((20, y_offset + 15), f"{i+1}.", fill=(255, 255, 255, 255))
            
            # Vẽ tên bài hát (cắt ngắn nếu quá dài)
            title = track['title']
            if len(title) > 40: title = title[:37] + "..."
            draw.text((50, y_offset + 5), title, fill=(255, 215, 0, 255))
            
            # Vẽ thời lượng hoặc nguồn
            duration = track.get('duration_string', 'N/A')
            draw.text((50, y_offset + 25), f"⏱️ {duration} | Uploader: {track.get('uploader', 'Ẩn')}", fill=(180, 180, 180, 255))
            
            # Khung phân cách
            draw.line([(20, y_offset + 50), (480, y_offset + 50)], fill=(60, 60, 60, 255))
            y_offset += 60
            
        # Xuất ảnh ra bộ nhớ đệm bytes
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    @commands.command(name="play")
    async def search(self, ctx, *, query: str):
        """Tìm kiếm nhạc trên YTB/SCL và trả về menu ảnh"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Việt ơi, bạn phải vào một phòng thoại (Voice Channel) trước đã!")
            return

        await ctx.send(f"🔍 Đang tìm kiếm bài hát: **{query}** trên hệ thống...")

        # Tiến hành cào dữ liệu search từ yt-dlp
        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            try:
                # Tìm tối đa 5 kết quả để tránh nghẽn luồng xử lý
                info = ydl.extract_info(f"ytsearch5:{query}", download=False)
                if 'entries' not in info or not info['entries']:
                    await ctx.send("❌ Không tìm thấy bài hát nào phù hợp rồi.")
                    return
                
                tracks = info['entries']
                self.search_results[ctx.author.id] = tracks # Lưu lại danh sách vào bộ nhớ tạm
                
                # Tạo menu ảnh bằng Pillow
                menu_buffer = self.create_menu_image(tracks)
                discord_file = discord.File(fp=menu_buffer, filename="music_menu.png")
                
                await ctx.send(content="👉 **Nhập số (1, 2, 3, 4, 5) để chọn bài hát bạn muốn phát:**", file=discord_file)

            except Exception as e:
                await ctx.send(f"❌ Lỗi khi tìm kiếm nhạc: {e}")

    # Bộ lắng nghe sự kiện chat để bắt số chọn bài hát rảnh tay giống hệt ảnh mẫu
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Kiểm tra xem user này có lịch sử search bài hát vừa gõ không
        author_id = message.author.id
        if author_id in self.search_results:
            content = message.content.strip()
            
            # Nếu user gõ một số hợp lệ từ 1 đến số bài hát tìm thấy
            if content.isdigit():
                choice = int(content) - 1
                tracks = self.search_results[author_id]
                
                if 0 <= choice < len(tracks):
                    selected_track = tracks[choice]
                    del self.search_results[author_id] # Xóa khỏi hàng đợi sau khi chọn xong
                    
                    ctx = await self.bot.get_context(message)
                    await self.play_audio(ctx, selected_track)

    async def play_audio(self, ctx, track):
        voice_channel = ctx.author.voice.channel
        
        try:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc:
                if vc.channel != voice_channel:
                    await vc.move_to(voice_channel)
            else:
                vc = await voice_channel.connect()

            if vc.is_playing():
                vc.stop()

            # Lấy luồng URL stream trực tiếp từ YTDL
            url = track['url']
            await ctx.send(f"🎶 Đang phát bài: **{track['title']}** vào phòng `{voice_channel.name}`")
            
            vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=url, **FFMPEG_OPTIONS))
            
        except Exception as e:
            await ctx.send(f"❌ Có lỗi xảy ra khi phát luồng nhạc: {e}")

async def setup(bot):
    await bot.add_cog(MusicBot(bot))