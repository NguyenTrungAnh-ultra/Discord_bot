import discord
from discord.ext import commands
import logging
import sys
from pathlib import Path
root_path = Path(__file__).resolve().parents[3]
sys.path.append(str(root_path))

import io
from src.modules.news_summarizer.scanners.tin_doanh_nghiep import VCI_news
from src.utils.text import clean_title, get_article
from src.modules.news_summarizer.ai_helper import tomtat100
from src.core.db.connection import AsyncDatabase
from src.modules.deep_research.company_graph import create_company_graph
from src.modules.deep_research.main_graph import create_research_graph
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

# Khởi tạo đồ thị phân tích RAG / Deep Research
company_analyst = create_company_graph()
research_analyst = create_research_graph()

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

@bot.command(
    name="profile",
    help="Phân tích sâu mô hình kinh doanh và tài chính của doanh nghiệp. Cú pháp: !profile <TICKER>. Ví dụ: !profile TCB"
)
async def profile(ctx, ticker: str):
    """
    Phân tích mô hình kinh doanh và tình hình tài chính của một doanh nghiệp.
    """
    ticker = ticker.strip().upper()
    if len(ticker) != 3 or not ticker.isalpha():
        await ctx.send("⚠️ Mã cổ phiếu không hợp lệ. Vui lòng nhập mã có 3 chữ cái. Ví dụ: `!profile TCB`")
        return
        
    status_msg = await ctx.send(f"⏳ **[1/3]** Đang kiểm tra dữ liệu cache & chuẩn bị phân tích cho **{ticker}**...")
    
    initial_state = {
        "ticker": ticker,
        "business_profile": None,
        "financial_data": None,
        "financial_insight": None,
        "final_memo": None,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_requests": 0,
        "node_tokens": {}
    }
    
    try:
        # Cập nhật trạng thái bắt đầu chạy LangGraph
        await status_msg.edit(content=f"🔄 **[2/3]** Đang tiến hành thu thập thông tin và chạy phân tích AI cho **{ticker}** (quá trình này có thể mất 1-2 phút)...")
        
        # Invoke LangGraph
        final_state = await company_analyst.ainvoke(initial_state)
        memo = final_state.get("final_memo")
        
        if memo:
            await status_msg.edit(content=f"✍️ **[3/3]** Đang tổng hợp và gửi báo cáo phân tích cho **{ticker}**...")
            
            # Gửi file Markdown đính kèm để không bị giới hạn 2000 ký tự
            file_data = io.BytesIO(memo.encode('utf-8'))
            discord_file = discord.File(fp=file_data, filename=f"Investment_Memo_{ticker}.md")
            
            # Gửi tệp tin đính kèm
            await ctx.send(
                content=f"✅ Đã hoàn thành báo cáo phân tích đầu tư cho **{ticker}**!",
                file=discord_file
            )
            await status_msg.delete()
        else:
            await status_msg.edit(content=f"❌ Không thể tạo báo cáo phân tích cho **{ticker}**.")
    except Exception as e:
        print(f"Lỗi lệnh profile: {e}")
        await status_msg.edit(content=f"❌ Đã xảy ra lỗi trong quá trình phân tích **{ticker}**: {e}")

@bot.command(
    name="research",
    help="Nghiên cứu vĩ mô hoặc ngành theo chủ đề yêu cầu. Cú pháp: !research <chủ đề>. Ví dụ: !research Lạm phát 2025"
)
async def research(ctx, *, query: str):
    """
    Nghiên cứu vĩ mô/ngành theo chủ đề tự do qua luồng RAG Agent.
    """
    query = query.strip()
    if not query:
        await ctx.send("⚠️ Vui lòng nhập chủ đề cần nghiên cứu. Ví dụ: `!research Lạm phát 2025`")
        return
        
    status_msg = await ctx.send(f"⏳ **[1/2]** Đang khởi động tiến trình nghiên cứu cho chủ đề: **'{query}'**...")
    
    initial_state = {
        "query": query,
        "search_queries": [],
        "urls": [],
        "current_url": None,
        "current_title": None,
        "current_content": None,
        "current_insight": None,
        "insights": [],
        "db_insights": None,
        "report": "",
        "iteration": 0,
        "max_iterations": 3
    }
    
    try:
        await status_msg.edit(content=f"🔄 **[2/2]** Đang cào thông tin web, thực hiện RAG và tổng hợp báo cáo cho: **'{query}'** (quá trình này mất khoảng 2-3 phút)...")
        
        final_state = await research_analyst.ainvoke(initial_state)
        report = final_state.get("report")
        
        if report:
            file_data = io.BytesIO(report.encode('utf-8'))
            discord_file = discord.File(fp=file_data, filename=f"Macro_Research_Report.md")
            await ctx.send(
                content=f"✅ Đã hoàn thành báo cáo nghiên cứu vĩ mô cho chủ đề: **'{query}'**!",
                file=discord_file
            )
            await status_msg.delete()
        else:
            await status_msg.edit(content=f"❌ Không thể sinh báo cáo nghiên cứu cho chủ đề: **'{query}'**.")
    except Exception as e:
        print(f"Lỗi lệnh research: {e}")
        await status_msg.edit(content=f"❌ Đã xảy ra lỗi trong quá trình nghiên cứu: {e}")

bot.run(token=token, log_handler=handler, log_level=logging.DEBUG)
