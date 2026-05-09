import discord
from discord.ext import commands
import requests
import os

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.environ.get('WEATHER_API_KEY')

    @commands.command(name="weather")
    async def weather(self, ctx, *, city: str):
        """Cú pháp: !weather <tên thành phố>"""
        if not self.api_key:
            await ctx.send("❌ Bot chưa được cấu hình API Key thời tiết!")
            return

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric&lang=vi"
        
        try:
            response = requests.get(url).json()
            
            if response.get("cod") != 200:
                await ctx.send(f"❌ Không tìm thấy thông tin cho: **{city}**")
                return

            # Trích xuất dữ liệu
            temp = response["main"]["temp"]
            feels_like = response["main"]["feels_like"]
            desc = response["weather"][0]["description"].capitalize()
            humidity = response["main"]["humidity"]
            wind = response["wind"]["speed"]
            city_name = response["name"]

            embed = discord.Embed(
                title=f"🌤️ Thời tiết tại {city_name}",
                description=f"**{desc}**",
                color=discord.Color.orange()
            )
            embed.add_field(name="Nhiệt độ", value=f"{temp}°C", inline=True)
            embed.add_field(name="Cảm giác như", value=f"{feels_like}°C", inline=True)
            embed.add_field(name="Độ ẩm", value=f"{humidity}%", inline=True)
            embed.add_field(name="Tốc độ gió", value=f"{wind} m/s", inline=True)
            embed.set_footer(text=f"Yêu cầu bởi {ctx.author.display_name}")
            
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Đã xảy ra lỗi khi lấy dữ liệu: {e}")

async def setup(bot):
    await bot.add_cog(Weather(bot))