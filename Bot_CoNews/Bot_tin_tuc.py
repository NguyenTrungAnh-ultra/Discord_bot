import discord
from discord.ext import commands
import logging
from News.config import DATA_FILE
from News.tin_doanh_nghiep import VCI_news
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random
import asyncio
import os

#Config
MIN_WAIT_SECONDS = 300 
MAX_WAIT_SECONDS = 600
CHANNEL_ID = 1445423293841805464
today = str(datetime.today().strftime('%Y-%m-%d'))

# Khởi tạo Bot
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"we are going in, {bot.user.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if "shit" in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention} - don't!")
    
    await bot.process_commands(message)

@bot.command()
async def tin_doanh_nghiep(ctx):
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            news_items = json.load(f)
            
            # Tạo Embed
            embed = discord.Embed(
                title="📰 Tin Tức Mới Nhất 📈",
                color=discord.Color.blue() # Chọn màu bạn thích
            )
            
            # Thêm tối đa 10 tin tức (vì Embed có giới hạn Field)
            for i, item in enumerate(news_items[:10]): 
                title = item['title']
                link = item['link']
                
                # Thêm Field cho mỗi tin tức
                # name là tiêu đề Field, value là nội dung Field
                embed.add_field(
                    name=f"{i+1}. {title}",
                    value=f"[Xem chi tiết tại đây]({link})",
                    inline=False # Mỗi tin tức trên một dòng riêng biệt
                )
                
            await ctx.send(embed=embed)

    except FileNotFoundError:
        await ctx.send(f"Lỗi: Không tìm thấy file dữ liệu.")
    except Exception as e:
        await ctx.send(f"Đã xảy ra lỗi: {e}")

@bot.command()
async def news(ctx = f'{today}, {today}'):
    date = [x.strip() for x in ctx.split(',')]
    if ctx:
        p = 1
        while True:
            NEWS = VCI_news().get_news(page=p, start_date=date[0], end_date=[-1])
            for new in NEWS:
                new.get()
                return VCI_news().get_news(page=p, start_date=date[0], end_date=[-1])
    

# chay bot
bot.run(token=token, log_handler=handler, log_level=logging.DEBUG)
