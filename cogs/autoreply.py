import discord
from discord.ext import commands
import os
import json

DB_FILE = "noprefix_db.json"
MEDIA_DIR = "./bot_media"

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

    def get_file_type(self, ext):
        ext = ext.lower()
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            return 'image'
        elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            return 'video'
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            return 'voice'
        return 'text'

    # ================= LỆNH HELP TỰ ĐỘNG CẬP NHẬT =================
    @commands.command(name="help")
    async def help_command(self, ctx):
        """Hiển thị bảng hướng dẫn sử dụng bot"""
        embed = discord.Embed(
            title="🤖 BẢNG HƯỚNG DẪN SỬ DỤNG BOT",
            description="Chào Việt! Dưới đây là danh sách các lệnh và từ khóa tự động hiện tại.",
            color=discord.Color.blue()
        )
        
        # Nhóm 1: Các lệnh quản lý hệ thống (Cần prefix !)
        admin_commands = (
            "`!img <từ khóa>`: Tìm kiếm hình ảnh trực tiếp qua Google API.\n"
            "`!refresh`: Làm mới toàn bộ hệ thống và cập nhật code/biến môi trường.\n"
            "`!noprefix <từ khóa>`: Tạo phản hồi tự động (Đính kèm file hoặc Reply).\n"
            "`!delprefix <từ khóa>`: Xóa từ khóa tự động đã tạo.\n"
            "`!listprefix`: Xem danh sách chi tiết cấu hình gốc."
        )
        embed.add_field(name="🛠️ LỆNH QUẢN LÝ (Cần dấu `!`)", value=admin_commands, inline=False)

        # Nhóm 2: Các từ khóa rảnh tay (Noprefix)
        if self.reply_database:
            keywords_list = []
            for k, v in self.reply_database.items():
                emoji = "🖼️" if v["type"] == "image" else "🎬" if v["type"] == "video" else "🔊" if v["type"] == "voice" else "📝"
                keywords_list.append(f"{emoji} `{k}`")
            
            noprefix_value = ", ".join(keywords_list)
        else:
            noprefix_value = "*Chưa có từ khóa nào được tạo. Hãy dùng lệnh `!noprefix` để thêm!*"

        embed.add_field(name="💬 TỪ KHÓA CHAT NHANH (Không cần dấu `!`)", value=noprefix_value, inline=False)
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name} • Hệ thống tự động kích hoạt")
        
        await ctx.send(embed=embed)

    # ================= CÁC LỆNH QUẢN LÝ KHÁC (Giữ nguyên luồng chuẩn) =================
    @commands.command(name="noprefix")
    @commands.has_permissions(administrator=True)
    async def noprefix(self, ctx, name: str, *, content: str = ""):
        keyword = name.lower().strip()
        attachment = None

        if ctx.message.reference and ctx.message.reference.message_id:
            try:
                replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                if replied_msg.attachments:
                    attachment = replied_msg.attachments[0]
            except Exception:
                pass

        if ctx.message.attachments:
            attachment = ctx.message.attachments[0]

        if attachment:
            file_extension = os.path.splitext(attachment.filename)[1]
            response_type = self.get_file_type(file_extension)
            local_filename = f"{keyword}{file_extension}"
            local_path = os.path.join(MEDIA_DIR, local_filename)

            await ctx.send(f"⏳ Đang tải và lưu media cho từ khóa `{keyword}`...")
            try:
                await attachment.save(local_path)
                self.reply_database[keyword] = {"type": response_type, "is_local": True, "content": local_path}
                self.save_database()
                await ctx.send(f"✅ Thành công! Chỉ cần gõ từ khóa `{keyword}` là dùng được ngay.")
                return
            except Exception as e:
                await ctx.send(f"❌ Lỗi tải file: {e}")
                return

        if not content:
            await ctx.send("❌ Bạn phải nhập link/chữ, đính kèm file hoặc reply tin nhắn!")
            return

        content_lower = content.lower()
        if any(ext in content_lower for ext in ['.png', '.jpg', '.jpeg', '.gif']):
            response_type = "image"
        elif any(ext in content_lower for ext in ['.mp4', '.webm', '.mov']):
            response_type = "video"
        elif any(ext in content_lower for ext in ['.mp3', '.wav']):
            response_type = "voice"
        else:
            response_type = "text"

        self.reply_database[keyword] = {"type": response_type, "is_local": False, "content": content}
        self.save_database()
        await ctx.send(f"✅ Đã lưu từ khóa bằng chuỗi/link!\n👉 Từ khóa: `{keyword}` | Loại: `{response_type}`")

    @commands.command(name="delprefix")
    @commands.has_permissions(administrator=True)
    async def delprefix(self, ctx, name: str):
        keyword = name.lower().strip()
        if keyword in self.reply_database:
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
            await ctx.send("📭 Chưa có từ khóa tự động nào.")
            return
        msg = "🤖 **Danh sách cấu hình gốc:**\n"
        for k, v in self.reply_database.items():
            source = "File lưu cục bộ" if v.get("is_local") else "Đường dẫn mạng"
            msg += f"• `{k}` ({v['type']} - {source})\n"
        await ctx.send(msg)

    # ================= BẮT SỰ KIỆN CHAT ĐỂ TỰ ĐỘNG REPLY VÀ NOPREFIX HELP =================
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        msg_content = message.content.strip().lower()

        # Cho phép gõ chữ "help" không dấu prefix vẫn mở được menu hướng dẫn
        if msg_content == "help":
            ctx = await self.bot.get_context(message)
            await self.help_command(ctx)
            return

        if msg_content in self.reply_database:
            data = self.reply_database[msg_content]
            res_type = data["type"]
            content = data["content"]
            is_local = data.get("is_local", False)

            if res_type == "text":
                await message.channel.send(content)
                return
            elif res_type in ["image", "video", "voice"]:
                if is_local:
                    if os.path.exists(content):
                        await message.channel.send(file=discord.File(content))
                    else:
                        await message.channel.send("❌ File này không tồn tại trên server.")
                else:
                    await message.channel.send(content)
                return

async def setup(bot):
    await bot.add_cog(AutoReply(bot))