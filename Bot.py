import discord
from discord.ext import commands
import logging
from News.config import DATA_FILE
from News.tin_doanh_nghiep import VCI_news
from News.tool import update_history, clean_title, get_artical
from gg_service.gemini import tomtat100
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
async def news(ctx, *, time_range: str = None):
    """
    Cách dùng:
    1. Mặc định là hôm nay
        !news
    2. Lấy tin tức của một ngày cụ thể Bạn nhập ngày theo định dạng Năm-Tháng-Ngày (YYYY-MM-DD).
        !news 2025-12-08
    3. Lấy tin tức trong khoảng thời gian Bạn nhập Ngày bắt đầu và Ngày kết thúc, ngăn cách nhau bằng dấu phẩy.
        !news 2025-12-01, 2025-12-09
    """
    # 1. Xử lý tham số ngày tháng
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    if time_range:
        # Tách chuỗi nhập vào: "2023-10-01, 2023-10-05" -> ['2023-10-01', '2023-10-05']
        date_list = [x.strip() for x in time_range.split(',')]
    else:
        # Mặc định là hôm nay
        date_list = [today_str, today_str]

    start_date = date_list[0]
    end_date = date_list[-1] # Lấy phần tử cuối cùng (nếu chỉ nhập 1 ngày thì start=end)

    # 2. Khởi tạo
    HISTORY_FILE = "/app/source/requested_news.json" 
    news_tool = VCI_news() # Khởi tạo 1 lần duy nhất
    requested_news = []
    page = 1
    total_count = 0

    await ctx.send(f"#####\n#####\n🔍 Đang tìm tin từ {start_date} đến {end_date}...\n#####\n#####")

    # 3. Vòng lặp lấy tin
    while True:
        # Gọi hàm lấy tin (Giả định hàm get_news của bạn đã hỗ trợ các tham số này)
        news_data = news_tool.get_news(
            page=page, 
            start_date=start_date, 
            end_date=end_date, 
            page_size=99
        )
        
        # Nếu không có dữ liệu trả về thì thoát vòng lặp
        if not news_data:
            await ctx.send('#####\n#####\n HET \n#####\n#####')
            print('#####\n#####\n HET \n#####\n#####')
            break

        # Gửi tin nhắn
        for item in reversed(news_data):
            title = item.get('news_title', 'Không tiêu đề')
            link = item.get('news_source_link', '#')
            source = item.get('news_from_name', 'VCI')
            time_str = item.get('update_date')
            sentiment = item.get('sentiment')

            # Gửi Webhook
            # Màu vang
            HEX_COLOR_VANG = 0xFF9900

            # Màu Đỏ đậm
            HEX_COLOR_DO = 0xEE0000

            # Nếu bạn muốn màu Xanh lá (Green)
            HEX_COLOR_XANH_LA = 0x00FF00
            # Tạo Embed
            if sentiment == 'Positive':
                embed = discord.Embed(
                    title=f"🔥 {title}", 
                    description=f"Nguồn: **{source}**\nThời gian: **{time_str}**",
                    url=link, 
                    color=HEX_COLOR_XANH_LA
                )
            elif sentiment == 'Negative':
                embed = discord.Embed(
                    title=f"🔥 {title}", 
                    description=f"Nguồn: **{source}**\nThời gian: **{time_str}**",
                    url=link, 
                    color=HEX_COLOR_DO
                )
            else :
                embed = discord.Embed(
                    title=f"🔥 {title}", 
                    description=f"Nguồn: **{source}**\nThời gian: **{time_str}**",
                    url=link, 
                    color=HEX_COLOR_VANG
                )
            
            await ctx.send(embed=embed)
            
            # Thêm vào danh sách lưu trữ
            requested_news.insert(0, item)
            total_count += 1
        
        page += 1

    # 4. Lưu lịch sử
    if total_count > 0:
        update_history(_list=requested_news, direct=HISTORY_FILE)
    else:
        await ctx.send("❌ Không tìm thấy tin nào trong khoảng thời gian này.")


@bot.command()
async def tomtat(ctx):
    """
    Reply tin nhắn tin tức -> Tìm trong JSON -> Trả vsề Link
    """
    # 1. Kiểm tra Reply
    if not ctx.message.reference:
        await ctx.send("⚠️ Vui lòng Reply vào tin nhắn tin tức cần lấy link.")
        return
    await ctx.send("chờ xíu bro...")
    try:
        # 2. Lấy nội dung tin nhắn gốc
        message_id = ctx.message.reference.message_id
        original_message = await ctx.channel.fetch_message(message_id)

        if not original_message.embeds:
            await ctx.send("❌ Tin nhắn này không có nội dung tin tức.")
            return

        # 3. Lấy Title từ Embed và làm sạch
        embed_title = original_message.embeds[0].title
        real_title = clean_title(embed_title)
        
        # Debug nhẹ để xem title bot đọc được là gì (có thể xóa sau này)
        print(f"Searching for title: {real_title}")

        # 4. Đọc file JSON lịch sử
        # Đảm bảo đường dẫn file đúng với biến HISTORY_FILE của bạn
        HISTORY_FILE = "./source/requested_news.json"
        
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                saved_news = json.load(f)
        except FileNotFoundError:
            await ctx.send("❌ Chưa có dữ liệu lịch sử nào được lưu.")
            return

        # 5. So sánh tìm Slug
        found_slug = None
        
        # Duyệt qua từng bài trong file json
        for item in saved_news:
            # So sánh tiêu đề trong JSON với tiêu đề lấy từ tin nhắn
            if item.get('news_title').strip() == real_title:
                found_slug = item.get('slug') 
                break
        
        # 6. Trả kết quả
        if found_slug:
            url = f"https://trading.vietcap.com.vn/ai-news/post-detail/{found_slug}?language=vi"
            art = await get_artical(link=url)
            print(art)
            sumarize = await tomtat100(artical=art)
            await ctx.send(f"{sumarize}")
            print('trả lời xong')
    except Exception as e:
        print(e)
        await ctx.send("Có lỗi xảy ra khi lấy link.")


# chay bot
bot.run(token=token, log_handler=handler, log_level=logging.DEBUG)

