import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
from PIL import Image, ImageDraw
from io import BytesIO

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'scsearch',
    'source_address': '0.0.0.0',
    'nocheckcertificate': True
}

class MusicView(discord.ui.View):
    """Bảng công cụ điều khiển nhạc bằng nút bấm trực quan"""
    def __init__(self, cog, guild_id):
        super().__init__(timeout=None) # Giữ nút bấm hoạt động vĩnh viễn không bị hết hạn
        self.cog = cog
        self.guild_id = guild_id

    # Đổi toàn bộ discord.Style thành discord.ButtonStyle
    @discord.ui.button(label="⏮️ Giảm Vol", style=discord.ButtonStyle.secondary)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.adjust_volume(interaction, self.guild_id, -0.2)

    @discord.ui.button(label="⏸️ Tạm Dừng", style=discord.ButtonStyle.primary)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = discord.utils.get(self.cog.bot.voice_clients, guild=interaction.guild)
        if not vc:
            await interaction.response.send_message("❌ Bot có đang ở trong phòng voice đâu Việt ơi.", ephemeral=True)
            return
        
        if vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Đang tạm dừng bài hát!", ephemeral=True)
        elif vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Tiếp tục phát nhạc!", ephemeral=True)

    @discord.ui.button(label="⏭️ Skip Bài", style=discord.ButtonStyle.danger)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = discord.utils.get(self.cog.bot.voice_clients, guild=interaction.guild)
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop() # Dừng bài cũ, sự kiện 'after' trong vc.play sẽ tự bốc bài tiếp theo
            await interaction.response.send_message("⏭️ Đã bỏ qua bài hát hiện tại!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Hiện tại không có bài nào đang phát để skip.", ephemeral=True)

    @discord.ui.button(label="⏭️ Tăng Vol", style=discord.ButtonStyle.secondary)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.adjust_volume(interaction, self.guild_id, 0.2)


class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.search_results = {}
        self.queues = {}       # Lưu danh sách hàng đợi theo từng Server: {guild_id: [track1, track2, ...]}
        self.volumes = {}      # Lưu mức âm lượng theo từng Server: {guild_id: current_volume_float}

    def create_menu_image(self, tracks):
        img_h = (len(tracks) * 60) + 60
        image = Image.new("RGBA", (500, img_h), (40, 40, 40, 255))
        draw = ImageDraw.Draw(image)
        
        draw.text((20, 15), "DANH SÁCH BÀI HÁT SOUNDCLOUD", fill=(255, 102, 0, 255))
        y_offset = 50
        for i, track in enumerate(tracks):
            draw.text((20, y_offset + 15), f"{i+1}.", fill=(255, 255, 255, 255))
            title = track.get('title', 'Unknown Title')
            if len(title) > 40: title = title[:37] + "..."
            draw.text((50, y_offset + 5), title, fill=(255, 215, 0, 255))
            duration = track.get('duration_string', 'N/A')
            uploader = track.get('uploader', 'SoundCloud Artist')
            draw.text((50, y_offset + 25), f"🎵 Artist: {uploader} | ⏱️ {duration}", fill=(180, 180, 180, 255))
            draw.line([(20, y_offset + 50), (480, y_offset + 50)], fill=(60, 60, 60, 255))
            y_offset += 60
            
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    # Đổi tên lệnh thành play theo yêu cầu của Việt
    @commands.command(name="play")
    async def play_command(self, ctx, *, query: str):
        """Tìm kiếm nhạc trên SoundCloud và trả về menu ảnh"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Việt ơi, bạn phải vào một phòng thoại (Voice Channel) trước đã nha!")
            return

        await ctx.send(f"🔍 Đang tìm kiếm bài hát: **{query}** trên SoundCloud...")

        with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(f"scsearch5:{query}", download=False)
                if 'entries' not in info or not info['entries']:
                    await ctx.send("❌ Không tìm thấy bài hát nào phù hợp.")
                    return
                
                tracks = info['entries']
                self.search_results[ctx.author.id] = tracks
                
                menu_buffer = self.create_menu_image(tracks)
                discord_file = discord.File(fp=menu_buffer, filename="sc_music_menu.png")
                await ctx.send(content="👉 **Nhập số (1, 2, 3, 4, 5) để chọn bài hát:**", file=discord_file)

            except Exception as e:
                await ctx.send(f"❌ Lỗi khi tìm kiếm nhạc: {e}")

    # Lệnh xem danh sách phát hiện tại hàng đợi
    @commands.command(name="queue")
    async def view_queue(self, ctx):
        """Xem danh sách các bài hát đang chờ phát tiếp theo"""
        guild_id = ctx.guild.id
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send("📭 Hàng đợi hiện tại đang trống rỗng Việt ơi!")
            return

        embed = discord.Embed(title="📜 DANH SÁCH BÀI HÁT ĐANG CHỜ", color=discord.Color.orange())
        queue_text = ""
        for idx, track in enumerate(self.queues[guild_id]):
            queue_text += f"**{idx+1}.** {track.get('title')} (⏱️ {track.get('duration_string', 'N/A')})\n"
        
        embed.description = queue_text
        await ctx.send(embed=embed)

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
                    
                    # Thêm bài hát vào hàng đợi thay vì phát đè ngay lập tức
                    guild_id = ctx.guild.id
                    if guild_id not in self.queues:
                        self.queues[guild_id] = []
                    self.queues[guild_id].append(selected_track)
                    
                    vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
                    if vc and vc.is_playing():
                        await ctx.send(f"➕ Đã thêm bài **{selected_track.get('title')}** vào hàng đợi danh sách phát! (Vị trí số: `{len(self.queues[guild_id])}`)")
                    else:
                        # Nếu bot đang rảnh, kích hoạt phát nhạc ngay bài đầu tiên
                        await self.check_queue_and_play(ctx)

    async def check_queue_and_play(self, ctx):
        guild_id = ctx.guild.id
        
        # Nếu hết bài trong hàng đợi
        if guild_id not in self.queues or not self.queues[guild_id]:
            return

        # Bốc bài hát đầu tiên ra khỏi danh sách chờ
        track = self.queues[guild_id].pop(0)
        voice_channel = ctx.author.voice.channel

        try:
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc:
                if vc.channel != voice_channel: await vc.move_to(voice_channel)
            else:
                vc = await voice_channel.connect()

            # Mặc định mức âm lượng ban đầu là 100% nếu chưa thiết lập
            if guild_id not in self.volumes:
                self.volumes[guild_id] = 1.0

            # Tạo bộ lọc âm lượng chuyên nghiệp cho Audio Source
            ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
            audio_source = discord.FFmpegPCMAudio(executable="ffmpeg", source=track['url'], **ffmpeg_options)
            
            # Biến đổi thành PCMVolumeTransformer để tăng giảm âm lượng động
            volume_source = discord.PCMVolumeTransformer(audio_source, volume=self.volumes[guild_id])

            # Hàm tự động kích hoạt khi bài hát kết thúc để bốc bài tiếp theo
            def after_playing(error):
                fut = asyncio.run_coroutine_threadsafe(self.check_queue_and_play(ctx), self.bot.loop)
                try:
                    fut.result()
                except Exception:
                    pass

            vc.play(volume_source, after=after_playing)

            # Đẩy Embed bảng công cụ điều khiển giao diện lên phòng chat kèm nút bấm
            embed = discord.Embed(title="🧡 ĐANG PHÁT NHẠC (SOUNDCLOUD)", color=discord.Color.green())
            embed.add_field(name="🎵 Bài hát", value=f"**{track.get('title')}**", inline=False)
            embed.add_field(name="🔊 Âm lượng hiện tại", value=f"`{int(self.volumes[guild_id] * 100)}%`", inline=True)
            embed.add_field(name="⏱️ Thời lượng", value=f"`{track.get('duration_string', 'N/A')}`", inline=True)
            
            view = MusicView(self, guild_id)
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            await ctx.send(f"❌ Lỗi khi phát nhạc từ hàng đợi: {e}")

    # Hàm logic phụ trách tăng giảm âm lượng khi bấm nút
    async def adjust_volume(self, interaction: discord.Interaction, guild_id, change):
        vc = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
        if not vc or not vc.source:
            await interaction.response.send_message("❌ Không có bài hát nào đang phát để chỉnh âm lượng!", ephemeral=True)
            return

        # Tính toán mức volume mới nằm trong khoảng giới hạn an toàn [0% đến 200%]
        new_vol = max(0.0, min(2.0, self.volumes.get(guild_id, 1.0) + change))
        self.volumes[guild_id] = new_vol
        
        # Áp dụng trực tiếp vào luồng phát của bot ngay lập tức
        vc.source.volume = new_vol
        
        await interaction.response.send_message(f"🔊 Đã chỉnh âm lượng lên: `{int(new_vol * 100)}%`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(MusicBot(bot))