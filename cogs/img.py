import discord
from discord.ext import commands
import requests
import os

class ImageSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Bot sẽ tự lấy mã từ Render khi Việt cài Environment Variables
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        self.cx = os.environ.get('SEARCH_ENGINE_ID')

    @commands.command(name="img")
    async def img(self, ctx, *, query: str):
        """Cú pháp: !img <từ khóa>"""
        if not self.api_key or not self.cx:
            await ctx.send("❌ Việt ơi, bạn chưa cài GOOGLE_API_KEY hoặc SEARCH_ENGINE_ID trên Render rồi!")
            return

        await ctx.send(f"🔍 Đang tìm ảnh cho: **{query}**...")

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'q': query,
            'cx': self.cx,
            'key': self.api_key,
            'searchType': 'image',
            'num': 1  # Lấy 1 ảnh chính xác nhất
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if "items" in data:
                img_url = data["items"][0]["link"]
                
                embed = discord.Embed(
                    title=f"🖼️ Kết quả của Việt: {query}",
                    color=discord.Color.blue()
                )
                embed.set_image(url=img_url)
                embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}")
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Không tìm thấy ảnh nào phù hợp rồi.")

        except Exception as e:
            await ctx.send(f"❌ Có lỗi xảy ra khi gọi Google API: {e}")

async def setup(bot):
    await bot.add_cog(ImageSearch(bot))