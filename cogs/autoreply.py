import discord
from discord.ext import commands
import os
import json
import requests

DB_FILE = "noprefix_db.json"
MEDIA_DIR = "./bot_media"

# Tạo thư mục lưu file nếu chưa có
if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

class AutoReply(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reply_database = self.load_database()

    def load_database(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_database(self):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.reply_database, f, ensure_ascii=False, indent=4)

    # ================= LỆNH TẠO NOPREFIX ĐỘNG =================
    @commands.command(name="noprefix")
    @commands.has_permissions(administrator=True)
    async def noprefix(self, ctx, name: str, response_type: str, *, content: str = ""):
        """
        Cú pháp 1 (Dùng Link): !noprefix <từ_khóa> <loại: image/video/voice/text> <link>
        Cú pháp 2 (Upload file trực tiếp): !noprefix <từ_khóa> <loại> (Bấm đính kèm file kèm theo)
        """
        response_type = response_type.lower().strip()
        keyword = name.lower().strip()

        if response_type not in ["image", "video", "voice", "text"]:
            await ctx.send("❌ Loại không hợp lệ! Chọn: `image`, `video`, `voice`, hoặc `text`.")
            return

        # TRƯỜNG HỢP 1: Việt đính kèm file trực tiếp từ máy tính/điện thoại
        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]
            # Lấy đuôi file (ví dụ: .jpg, .mp4, .mp3)
            file_extension = os.path.splitext(attachment.filename)[1]
            local_filename = f"{keyword}_{response_type}{file_extension}"
            local_path = os.path.join(MEDIA_DIR, local_filename)

            await ctx.send(f"⏳ Đang tải và lưu file `{attachment.filename}` về server...")
            
            # Tải file về và lưu vào thư mục bot_media trên Render
            try:
                await attachment.save(local_path)
                self.reply_database[keyword] = {
                    "type": response_type,
                    "is_local": True,
                    "content": local_path
                }
                self.save_database()
                await ctx.send(f"✅ Đã lưu file thành công! Từ giờ gõ `{keyword}` để kích hoạt.")
                return
            except Exception as e:
                await ctx.send(f"❌ Lỗi khi tải file: {e}")
                return

        # TRƯỜNG HỢP 2: Việt truyền Link có sẵn từ mạng vào
        if not content:
            await ctx.send("❌ Việt ơi, bạn phải nhập link hoặc đính kèm một file video/ảnh/audio chứ!")
            return

        self.reply_database[keyword] = {
            "type": response_type,
            "is_local": False,
            "content": content
        }
        self.save_database()
        await ctx.send(f"✅ Đã lưu từ khóa bằng Link thành công!\n👉 Từ khóa: `{keyword}` | Loại: `{response_type}`")

    # ================= LỆNH XÓA TỪ KHÓA =================
    @commands.command(name="delprefix")
    @commands.has_permissions(administrator=True)
    async def delprefix(self, ctx, name: str):
        keyword = name.lower().strip()
        if keyword in self.reply_database:
            # Nếu là file local thì xóa file đi cho nhẹ máy
            if self.reply_database[keyword].get("is_local"):
                file_path = self.reply_database[keyword]["content"]
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            del self.reply_database[keyword]
            self.save_database()
            await ctx.send(f"🗑️ Đã xóa từ khóa `{keyword}`.")
        else:
            await ctx.send(f"❌ Không tìm thấy từ khóa `{keyword}`.")

    @commands.command(name="listprefix")
    async def listprefix(self, ctx):
        if not self.reply_database:
            await ctx.send("📭 Chưa có từ khóa tự động nào Việt ơi.")
            return
        msg = "🤖 **Danh sách từ khóa phản hồi tự động:**\n"
        for k, v in self.reply_database.items():
            source = "File tải lên" if v.get("is_local") else "Link mạng"
            msg += f"• `{k}` ({v['type']} - {source})\n"
        await ctx.send(msg)

    # ================= BẮT SỰ KIỆN CHAT KHÔNG PREFIX =================
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        msg_content = message.content.strip().lower()

        if msg_content in self.reply_database:
            data = self.reply_database[msg_content]
            res_type = data["type"]
            content = data["content"]
            is_local = data.get("is_local", False)

            # 1. PHẢN HỒI TEXT
            if res_type == "text":
                await message.channel.send(content)
                return

            # 2. PHẢN HỒI HÌNH ẢNH HOẶC VIDEO
            elif res_type in ["image", "video"]:
                if is_local:
                    # Nếu là file lưu trên server, gửi đính kèm lên Discord
                    if os.path.exists(content):
                        await message.channel.send(file=discord.File(content))
                    else:
                        await message.channel.send("❌ File này bị mất trên server rồi Việt ơi!")
                else:
                    # Nếu là link, chỉ cần gửi embed hoặc gửi thẳng link để Discord tự hiện
                    await message.channel.send(content)
                return

            # 3. PHẢN HỒI VOICE (Gửi file âm thanh nghe trực tiếp)
            elif res_type == "voice":
                if is_local:
                    if os.path.exists(content):
                        # Gửi file .mp3/.wav lên, người dùng bấm nút Play nghe ngay trên đoạn chat!
                        await message.channel.send(file=discord.File(content))
                    else:
                        await message.channel.send("❌ File âm thanh không tồn tại trên server.")
                else:
                    # Gửi link âm thanh ra
                    await message.channel.send(f"🎵 Link nhạc/voice của Việt: {content}")

async def setup(bot):
    await bot.add_cog(AutoReply(bot))