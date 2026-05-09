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
        embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}") # Hiện tên người gọi lệnh
        await ctx.send(embed=embed)
    @commands.command()
    async def uptime(self, ctx):
        delta = datetime.datetime.now() - self.start_time
        await ctx.send(f"🚀 Bot đã online: `{delta.days}d, {delta.seconds//3600}h...`")

async def setup(bot):
    await bot.add_cog(General(bot))