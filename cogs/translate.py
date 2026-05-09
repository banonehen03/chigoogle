import discord
from discord.ext import commands
from deep_translator import GoogleTranslator

class Translate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="trans")
    async def trans(self, ctx, lang_to: str, *, text: str):
        """Cú pháp: !trans <mã_ngôn_ngữ> <nội dung>"""
        try:
            # Thực hiện dịch thuật bằng GoogleTranslator (miễn phí và ổn định)
            translated = GoogleTranslator(source='auto', target=lang_to).translate(text)
            
            embed = discord.Embed(
                title="🌍 Kết quả dịch thuật",
                color=discord.Color.blue()
            )
            embed.add_field(name="Văn bản gốc", value=text, inline=False)
            embed.add_field(name=f"Dịch sang: {lang_to.upper()}", value=translated, inline=False)
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Lỗi: Có thể mã ngôn ngữ '{lang_to}' không hỗ trợ hoặc có lỗi kết nối.")

async def setup(bot):
    await bot.add_cog(Translate(bot))