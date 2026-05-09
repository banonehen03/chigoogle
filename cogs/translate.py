import discord
from discord.ext import commands
from googletrans import Translator

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()

    @commands.command()
    async def trans(self, ctx, lang_to: str, *, text: str):
        """Cú pháp: !trans <mã_ngôn_ngữ> <nội dung>"""
        try:
            # Thực hiện dịch thuật
            result = self.translator.translate(text, dest=lang_to)
            
            embed = discord.Embed(
                title="🌍 Kết quả dịch thuật",
                color=discord.Color.blue()
            )
            embed.add_field(name=f"Gốc ({result.src})", value=text, inline=False)
            embed.add_field(name=f"Dịch sang ({result.dest})", value=result.text, inline=False)
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Lỗi: Có thể mã ngôn ngữ '{lang_to}' không đúng. (Ví dụ: vi, en, ja, ko...)")

async def setup(bot):
    await bot.add_cog(Translate(bot))