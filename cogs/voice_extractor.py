import discord
from discord.ext import commands
import os
import json
from moviepy.editor import VideoFileClip

# Sử dụng chung file database json và thư mục lưu trữ media với autoreply
DB_FILE = "noprefix_db.json"
MEDIA_DIR = "./bot_media"

if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

class VoiceExtractor(commands.Cog):
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

    def save_database(self, database):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=4)

    # ================= LỆNH TÁCH VOICE TỪ VIDEO =================
    @commands.command(name="getvoice")
    @commands.has_permissions(administrator=True)
    async def getvoice(self, ctx, name: str):
        """
        Cú pháp:
        Cách 1: !getvoice <từ_khóa> (Bấm reply vào tin nhắn chứa video)
        Cách 2: !getvoice <từ_khóa> (Đính kèm video trực tiếp rồi gõ lệnh)
        """
        keyword = name.lower().strip()
        attachment = None

        # 1. Kiểm tra xem có reply tin nhắn chứa video không
        if ctx.message.reference and ctx.message.reference.message_id:
            try:
                replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                if replied_msg.attachments:
                    attachment = replied_msg.attachments[0]
            except Exception:
                pass

        # 2. Kiểm tra xem có đính kèm video trực tiếp không
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]

        if not attachment:
            await ctx.send("❌ Việt ơi, bạn phải đính kèm video hoặc reply một tin nhắn chứa video chứ!")
            return

        # Kiểm tra đuôi file video
        file_extension = os.path.splitext(attachment.filename)[1].lower()
        if file_extension not in ['.mp4', '.mov', '.avi', '.webm']:
            await ctx.send("❌ File này không phải định dạng video hỗ trợ (mp4, mov, avi, webm)!")
            return

        await ctx.send(f"⏳ Đang tải video `{attachment.filename}` về hệ thống để xử lý...")

        temp_video_path = os.path.join(MEDIA_DIR, f"temp_{keyword}{file_extension}")
        final_mp3_path = os.path.join(MEDIA_DIR, f"{keyword}_voice.mp3")

        try:
            # Tải video tạm về server Render
            await attachment.save(temp_video_path)
            
            msg_processing = await ctx.send("🎬 Đang tách âm thanh từ video, Việt chờ một xíu nhé...")

            # Dùng moviepy để trích xuất audio
            video_clip = VideoFileClip(temp_video_path)
            audio_clip = video_clip.audio
            audio_clip.write_audiofile(final_mp3_path, logger=None)
            
            # Giải phóng RAM cho server
            audio_clip.close()
            video_clip.close()

            # Xóa file video gốc tạm thời đi cho nhẹ dung lượng
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)

            # Nạp dữ liệu cũ vào, thêm từ khóa mới rồi lưu lại vào json để file autoreply.py tự đọc được
            current_db = self.load_database()
            current_db[keyword] = {
                "type": "voice",
                "is_local": True,
                "content": final_mp3_path
            }
            self.save_database(current_db)

            await msg_processing.delete()
            await ctx.send(f"🔊 **Thành công rực rỡ!** Đã trích xuất xong âm thanh từ video.\n👉 Từ giờ chỉ cần gõ từ khóa `{keyword}` (không cần prefix) là bot tự gửi file âm thanh này lên chat.")

        except Exception as e:
            await ctx.send(f"❌ Thất bại khi xử lý tách âm thanh: {e}")
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)

async def setup(bot):
    await bot.add_cog(VoiceExtractor(bot))