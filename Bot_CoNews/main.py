import discord
from discord.ext import commands
import logging
from News.config import DATA_FILE
from News.tin_doanh_nghiep import run
import json
from dotenv import load_dotenv
import random
import asyncio
import os

#Config
MIN_WAIT_SECONDS = 300 
MAX_WAIT_SECONDS = 600
CHANNEL_ID = 1445423293841805464

# Khởi tạo Bot
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def background_loop_task():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)

    while not bot.is_closed():
        print("---------- Bắt đầu quét tin tức ----------")
        
        # --- QUAN TRỌNG: Chạy hàm run() trong một luồng riêng (Executor) ---
        # Điều này giúp Bot không bị đơ khi Playwright đang cào dữ liệu
        try:
            # run_in_executor trả về Future, ta dùng await để đợi kết quả mà không chặn bot
            is_sth = await bot.loop.run_in_executor(None, run)
        except Exception as e:
            print(f"Lỗi khi chạy run(): {e}")
            is_sth = False

        # --- Xử lý kết quả ---
        if is_sth:
            print(f"Tìm thấy {len(is_sth)} tin mới. Đang gửi...")
            for item in is_sth:
                try:
                    # Gửi từng tin một cho đẹp (hoặc gom vào Embed)
                    # Lưu ý: channel.send không nhận dict trực tiếp, phải format string
                    await channel.send(f"**{item['title']}**\n{item['link']}")
                    await asyncio.sleep(1) # Nghỉ 1 xíu giữa các tin để tránh spam rate limit
                except Exception as e:
                    print(f"Lỗi gửi tin nhắn: {e}")
        else:
            print("Không có tin tức mới.")

        # --- Tính toán thời gian ngủ ---
        sleep_time = random.randint(MIN_WAIT_SECONDS, MAX_WAIT_SECONDS)
        print(f"💤 Sẽ ngủ trong {sleep_time} giây...")
        print("------------------------------------------")

        await asyncio.sleep(sleep_time)

@bot.event
async def on_ready():
    print(f"we are going in, {bot.user.name}")

    bot.loop.create_task(background_loop_task())

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


bot.run(token=token, log_handler=handler, log_level=logging.DEBUG)
