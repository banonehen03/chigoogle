import discord
from discord.ext import commands
import datetime

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.now()

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(
            title="📚 Hướng dẫn sử dụng Chị Google", 
            color=discord.Color.blue(),
            description="Dưới đây là các lệnh bạn có thể dùng:"
        )
        embed.add_field(name="`!say <nội dung>`", value="Chị Google sẽ nói nội dung này trong voice.", inline=False)
        embed.add_field(name="`!uptime`", value="Xem thời gian bot đã hoạt động.", inline=False)
        embed.add_field(name="`!wiki <từ khóa>`", value="Tìm kiếm thông tin nhanh từ Wikipedia tiếng Việt.", inline=False)
        embed.add_field(name="`!trans <mã_ngôn_ngữ> <nội dung>`", value="Dịch văn bản (Mã: vi, en, ja, ko, zh-cn...)", inline=False)
        embed.add_field(name="`!weather <nội dung>`", value="xem dự báo thời tiết", inline=False)
        embed.add_field(name="`!calc <phép tính>`", value="Tính toán nhanh (Ví dụ: !calc (150+50)*2 )", inline=False)
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}") # Hiện tên người gọi lệnh
        await ctx.send(embed=embed)
    @commands.command()
    async def uptime(self, ctx):
        delta = datetime.datetime.now() - self.start_time
        await ctx.send(f"🚀 Bot đã online: `{delta.days}d, {delta.seconds//3600}h...`")

async def setup(bot):
    await bot.add_cog(General(bot))