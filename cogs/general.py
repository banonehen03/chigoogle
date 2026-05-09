import discord
from discord.ext import commands
import datetime

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.now()

    @commands.command()
    async def help(self, ctx):
        embed = discord.Embed(title="📚 Hướng dẫn sử dụng", color=discord.Color.blue())
        embed.add_field(name="!say", value="Nói nội dung yêu cầu", inline=False)
        embed.add_field(name="!uptime", value="Xem thời gian online", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    async def uptime(self, ctx):
        delta = datetime.datetime.now() - self.start_time
        await ctx.send(f"🚀 Bot đã online: `{delta.days}d, {delta.seconds//3600}h...`")

async def setup(bot):
    await bot.add_cog(General(bot))