import discord
from discord.ext import commands
import requests
import random
import re

class ImageSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="img")
    async def img(self, ctx, *, query: str):
        """Cú pháp: !img <từ khóa>"""
        await ctx.send(f"🔍 Đang tìm ảnh cho: **{query}**...")

        # Sử dụng DuckDuckGo để tìm kiếm ảnh nhanh (không cần API Key)
        url = 'https://duckduckgo.com/'
        params = {'q': query}

        try:
            # Bước 1: Lấy Token từ DuckDuckGo
            res = requests.post(url, data=params)
            search_obj = re.search(r'vqd=([\d-]+)\&', res.text, re.M | re.I)
            
            if not search_obj:
                await ctx.send("❌ Không thể lấy dữ liệu tìm kiếm.")
                return

            headers = {
                'authority': 'duckduckgo.com',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'referer': 'https://duckduckgo.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }

            params = (
                ('l', 'us-en'),
                ('o', 'json'),
                ('q', query),
                ('vqd', search_obj.group(1)),
                ('f', ',,,,'),
                ('p', '1'),
            )

            # Bước 2: Gọi API lấy danh sách ảnh
            request_url = 'https://duckduckgo.com/i.js'
            response = requests.get(request_url, headers=headers, params=params)
            data = response.json()

            if "results" in data and len(data["results"]) > 0:
                # Lấy ngẫu nhiên 1 trong 5 ảnh đầu tiên để đa dạng
                random_img = random.choice(data["results"][:5])
                img_url = random_img["image"]

                embed = discord.Embed(
                    title=f"🖼️ Kết quả cho: {query}",
                    color=discord.Color.purple()
                )
                embed.set_image(url=img_url)
                embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}")
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Không tìm thấy ảnh nào phù hợp rồi Việt ơi.")

        except Exception as e:
            await ctx.send(f"❌ Có lỗi xảy ra: {e}")

async def setup(bot):
    await bot.add_cog(ImageSearch(bot))