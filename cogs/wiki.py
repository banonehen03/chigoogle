import discord
from discord.ext import commands
import wikipedia

class Wiki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Thiết lập ngôn ngữ tiếng Việt cho Wikipedia
        wikipedia.set_lang("vi")

    @commands.command()
    async def wiki(self, ctx, *, query: str):
        await ctx.send(f"🔍 Đang tìm kiếm '{query}' trên Wikipedia...")
        
        try:
            # Lấy tóm tắt nội dung (giới hạn 3 câu để không bị quá dài)
            summary = wikipedia.summary(query, sentences=3)
            # Lấy thông tin trang để lấy URL
            page = wikipedia.page(query)

            embed = discord.Embed(
                title=f"Kết quả cho: {page.title}",
                description=summary,
                color=discord.Color.green(),
                url=page.url
            )
            embed.set_footer(text="Nguồn: Wikipedia")
            await ctx.send(embed=embed)

        except wikipedia.exceptions.DisambiguationError as e:
            # Trường hợp có nhiều kết quả trùng tên
            options = "\n".join(e.options[:5])
            await ctx.send(f"❌ Có quá nhiều kết quả. Bạn hãy thử tìm cụ thể hơn: \n`{options}`")
        except wikipedia.exceptions.PageError:
            # Trường hợp không tìm thấy trang nào
            await ctx.send(f"❌ Không tìm thấy thông tin về '{query}' trên Wikipedia.")
        except Exception as e:
            await ctx.send(f"❌ Đã xảy ra lỗi: {e}")

async def setup(bot):
    await bot.add_cog(Wiki(bot))