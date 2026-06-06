import discord
from discord.ext import commands
import logging
import sys
from pathlib import Path
root_path = Path(__file__).resolve().parents[3]
sys.path.append(str(root_path))

from src.modules.news_summarizer.scanners.tin_doanh_nghiep import VCI_news
from src.utils.text import clean_title, get_article
from src.modules.news_summarizer.ai_helper import tomtat100
from src.core.db.connection import AsyncDatabase
from dotenv import load_dotenv
from datetime import datetime
import os

# Khởi tạo Bot
env_path = Path(__file__).resolve().parents[3] / '.env'
load_dotenv(dotenv_path=env_path)
token = os.getenv('DISCORD_TOKEN')
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Kiểm tra xem phiên bản discord.py có hỗ trợ threads không để tránh crash
if hasattr(intents, 'threads'):
    intents.threads = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot đã sẵn sàng: {bot.user.name}")
    print(f"ID Bot: {bot.user.id}")
    print("------")

@bot.event
async def on_message(message):
    print(f"📩 Nhận tin nhắn từ {message.author}: '{message.content}' (Channel: {message.channel.name})")
    if message.author == bot.user:
        return
    if "shit" in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention} - don't!")
    
    await bot.process_commands(message)

@bot.event
async def on_guild_join(guild):
    print(f"✅ [Bot] Joined new guild: {guild.name} (ID: {guild.id})")
    try:
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            await guild.system_channel.send("Hello! Thanks for inviting me. Type `!news` to see the latest updates.")
    except Exception as e:
        print(f"⚠️ Could not send welcome message in {guild.name}: {e}")

@bot.event
async def on_thread_join(thread):
    print(f"✅ [Bot] Joined new thread/room: {thread.name} (ID: {thread.id})")
    try:
        await thread.join()
        if thread.permissions_for(thread.guild.me).send_messages:
            await thread.send(f"Chào mọi người! Mình đã tham gia vào thread **{thread.name}**. Gõ `!news` nếu cần mình nhé!")
    except Exception as e:
        print(f"⚠️ Lỗi khi tham gia thread {thread.name}: {e}")

@bot.command()
async def news(ctx, *, time_range: str = None):
    """
    !news [YYYY-MM-DD] hoặc !news [YYYY-MM-DD, YYYY-MM-DD]
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    if time_range:
        date_list = [x.strip() for x in time_range.split(',')]
    else:
        date_list = [today_str, today_str]

    start_date = date_list[0]
    end_date = date_list[-1]

    news_tool = VCI_news()
    page = 1
    total_count = 0

    await ctx.send(f"#####\n#####\n🔍 Đang tìm tin từ {start_date} đến {end_date}...\n#####\n#####")

    while True:
        news_data = news_tool.get_news(
            page=page, 
            start_date=start_date, 
            end_date=end_date, 
            page_size=99
        )
        
        if not news_data:
            await ctx.send('#####\n#####\n HET \n#####\n#####')
            break

        for item in reversed(news_data):
            title = item.get('news_title', 'Không tiêu đề')
            link = item.get('news_source_link', '#')
            source = item.get('news_from_name', 'VCI')
            time_str = item.get('update_date')
            sentiment = item.get('sentiment')

            # Colors
            HEX_COLOR_VANG = 0xFF9900
            HEX_COLOR_DO = 0xEE0000
            HEX_COLOR_XANH_LA = 0x00FF00

            if sentiment == 'Positive':
                embed_color = HEX_COLOR_XANH_LA
            elif sentiment == 'Negative':
                embed_color = HEX_COLOR_DO
            else:
                embed_color = HEX_COLOR_VANG

            embed = discord.Embed(
                title=f"🔥 {title}", 
                description=f"Nguồn: **{source}**\nThời gian: **{time_str}**",
                url=link, 
                color=embed_color
            )
            
            await ctx.send(embed=embed)
            
            # Lưu vào Database trực tiếp
            insert_query = """
                INSERT INTO news (id, news_title, ticker, news_source_link, news_from_name, update_date, sentiment, news_short_content, slug)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO NOTHING
            """
            try:
                await AsyncDatabase.execute_query(insert_query, 
                    item.get('id'), title, item.get('ticker'), link, source, 
                    time_str, sentiment, item.get('news_short_content'), item.get('slug')
                )
            except Exception as e:
                print(f"Lỗi khi lưu tin vào DB: {e}")
            
            total_count += 1
        
        page += 1

    if total_count == 0:
        await ctx.send("❌ Không tìm thấy tin nào trong khoảng thời gian này.")

@bot.command()
async def tomtat(ctx):
    """
    Reply tin nhắn tin tức -> Tìm trong DB -> Tóm tắt
    """
    if not ctx.message.reference:
        await ctx.send("⚠️ Vui lòng Reply vào tin nhắn tin tức cần lấy link.")
        return
    await ctx.send("chờ xíu bro...")

    try:
        message_id = ctx.message.reference.message_id
        original_message = await ctx.channel.fetch_message(message_id)

        if not original_message.embeds:
            await ctx.send("❌ Tin nhắn này không có nội dung tin tức.")
            return

        embed_title = original_message.embeds[0].title
        real_title = clean_title(embed_title)
        
        print(f"Searching for title in DB: {real_title}")

        # Tìm Slug trong Database
        query = "SELECT slug FROM news WHERE news_title = $1 LIMIT 1"
        records = await AsyncDatabase.fetch_query(query, real_title)
        
        found_slug = records[0]['slug'] if records else None
        
        if found_slug:
            url = f"https://trading.vietcap.com.vn/ai-news/post-detail/{found_slug}?language=vi"
            art = await get_article(link=url)
            sumarize = await tomtat100(artical=art)
            await ctx.send(f"{sumarize}")
        else:
            await ctx.send("❌ Không tìm thấy thông tin tin tức này trong Database.")

    except Exception as e:
        print(f"Lỗi tóm tắt: {e}")
        await ctx.send("Có lỗi xảy ra khi lấy link.")

@bot.command()
async def cleanup(ctx, limit: int = 500):
    """Quét và xóa các tin nhắn trùng lặp link trong channel"""
    status_msg = await ctx.send(f"🧹 Đang bắt đầu quét {limit} tin nhắn gần nhất...")
    
    seen_urls = set()
    deleted_count = 0
    error_count = 0
    
    try:
        async for message in ctx.channel.history(limit=limit):
            if (message.author == bot.user or message.webhook_id is not None) and message.embeds:
                if message.id == status_msg.id:
                    continue
                    
                for embed in message.embeds:
                    if embed.url:
                        if embed.url in seen_urls:
                            try:
                                await message.delete()
                                deleted_count += 1
                            except Exception as e:
                                error_count += 1
                        else:
                            seen_urls.add(embed.url)
        
        report = f"✅ Đã dọn dẹp xong! Xóa {deleted_count} tin nhắn trùng lặp."
        if error_count > 0:
            report += f"\n⚠️ Không thể xóa {error_count} tin nhắn."
        await status_msg.edit(content=report)
        
    except Exception as e:
        await ctx.send(f"❌ Có lỗi xảy ra khi dọn dẹp: {e}")

bot.run(token=token, log_handler=handler, log_level=logging.DEBUG)
