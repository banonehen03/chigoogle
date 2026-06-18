import discord
from discord.ext import commands
import os
import json

DB_FILE = "noprefix_db.json"

class VoicePlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_database(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @commands.command(name="speak")
    @commands.has_permissions(administrator=True)
    async def speak(self, ctx, keyword: str = None):
        """
        Cú pháp:
        Cách 1 (Gửi trực tiếp): !speak + Đính kèm file âm thanh (.mp3, .wav)
        Cách 2 (Reply từ khóa rảnh tay): !speak <tên_từ_khóa> (Ví dụ: !speak alo)
        Cách 3 (Reply file âm thanh): !speak (Bấm reply vào tin nhắn chứa file âm thanh của người khác)
        """
        audio_source = None
        is_temp_file = False

        # 1. KIỂM TRA XEM NGƯỜI DÙNG CÓ TRONG PHÒNG VOICE KHÔNG
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Việt ơi, bạn phải vào một phòng thoại (Voice Channel) trước thì bot mới vào đọc được chứ!")
            return

        voice_channel = ctx.author.voice.channel

        # 2. TRƯỜNG HỢP 1: ĐÍNH KÈM FILE HOẶC REPLY TIN NHẮN CÓ FILE ÂM THANH
        attachment = None
        # Check nếu đính kèm trực tiếp
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
        # Check nếu reply tin nhắn có file
        elif ctx.message.reference and ctx.message.reference.message_id:
            try:
                replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                if replied_msg.attachments:
                    attachment = replied_msg.attachments[0]
            except Exception:
                pass

        if attachment:
            file_extension = os.path.splitext(attachment.filename)[1].lower()
            if file_extension not in ['.mp3', '.wav', '.ogg', '.m4a']:
                await ctx.send("❌ Định dạng âm thanh không hỗ trợ! Bot chỉ đọc được file .mp3, .wav, .ogg, .m4a.")
                return
            
            # Tải file tạm về để phát
            audio_source = f"./bot_media/temp_speak{file_extension}"
            await attachment.save(audio_source)
            is_temp_file = True

        # 3. TRƯỜNG HỢP 2: GÕ TÊN TỪ KHÓA ĐÃ LƯU TRONG DATABASE (Ví dụ: !speak alo)
        elif keyword:
            db = self.load_database()
            kw_clean = keyword.lower().strip()
            if kw_clean in db and db[kw_clean]["type"] == "voice" and db[kw_clean].get("is_local"):
                audio_source = db[kw_clean]["content"]
            else:
                await ctx.send(f"❌ Không tìm thấy từ khóa voice nào tên là `{keyword}` trong database cục bộ!")
                return
        
        # Nếu quét cả 2 trường hợp mà vẫn không có nguồn âm thanh
        if not audio_source or not os.path.exists(audio_source):
            await ctx.send("❌ Thiếu nguồn âm thanh! Hãy đính kèm file, gõ tên từ khóa voice hoặc reply tin nhắn có chứa file voice nhé.")
            return

        # 4. LUỒNG ĐIỀU KHIỂN BOT VÀO PHÒNG VOICE VÀ PHÁT NHẠC
        try:
            # Kiểm tra xem bot đã ở trong phòng voice nào chưa
            vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if vc:
                # Nếu đang ở phòng khác thì chuyển sang phòng của Việt
                if vc.channel != voice_channel:
                    await vc.move_to(voice_channel)
            else:
                # Nếu chưa vào thì tiến hành kết nối
                vc = await voice_channel.connect()

            # Nếu bot đang phát âm thanh khác thì dừng lại để phát cái mới
            if vc.is_playing():
                vc.stop()

            await ctx.send(f"🔊 Chị Google đang tiến vào phòng `{voice_channel.name}` để phát âm thanh...")

            # Hàm callback để tự động xóa file tạm sau khi phát xong (tránh nặng server Render)
            def after_playing(error):
                if is_temp_file and os.path.exists(audio_source):
                    try:
                        os.remove(audio_source)
                    except Exception:
                        pass

            # Phát âm thanh bằng FFmpeg
            vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=audio_source), after=after_playing)

        except Exception as e:
            await ctx.send(f"❌ Có lỗi xảy ra khi kết nối hoặc phát Voice: {e}")
            if is_temp_file and os.path.exists(audio_source):
                os.remove(audio_source)

    # LỆNH CHO BOT RỜI PHÒNG VOICE KHẨN CẤP
    @commands.command(name="leave")
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx):
        """Kích bot rời khỏi phòng thoại"""
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if vc:
            await vc.disconnect()
            await ctx.send("👋 Đã rời khỏi phòng thoại sạch sẽ!")
        else:
            await ctx.send("❌ Hiện tại bot có đang ở trong phòng voice nào đâu Việt ơi.")

async def setup(bot):
    await bot.add_cog(VoicePlayer(bot))