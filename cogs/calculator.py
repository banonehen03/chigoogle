import discord
from discord.ext import commands
import re

class Calculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="calc")
    async def calc(self, ctx, *, expression: str):
        try:
            # 1. Lọc ký tự an toàn
            safe_string = re.sub(r'[^0-9+\-*/().\s]', '', expression)
            
            # 2. Tính toán
            result = eval(safe_string, {"__builtins__": None}, {})
            
            if isinstance(result, float):
                result = round(result, 4)

            embed = discord.Embed(
                title="🧮 Máy tính của Chị Google",
                color=discord.Color.teal()
            )
            embed.add_field(name="Phép tính:", value=f"```python\n{expression}\n```", inline=False)
            embed.add_field(name="Kết quả:", value=f"```fix\n{result}```", inline=False)
            embed.set_footer(text=f"Tính toán cho {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except ZeroDivisionError:
            await ctx.send(f"❌ {ctx.author.display_name} ơi, không thể chia cho số 0!")
        except Exception:
            await ctx.send("❌ Phép tính không hợp lệ! Việt kiểm tra lại nhé.")

async def setup(bot):
    await bot.add_cog(Calculator(bot))