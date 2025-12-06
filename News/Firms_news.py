import json
import os
import requests
from datetime import datetime
from core.utils.user_agent import get_headers
import discord
from discord.ext import commands, tasks # Import thêm tasks để chạy vòng lặp
import logging
from dotenv import load_dotenv

# --- CẤU HÌNH ---
format = "%Y-%m-%d %H:%M:%S"
MIN_WAIT_SECONDS = 300 
CHANNEL_ID = 1445423293841805464
HISTORY_LIMIT = 10 # Tăng nhẹ limit để check kỹ hơn

class VCI_news:
    def __init__(self):
        self.url = "https://ai.vietcap.com.vn/api/v2/news_info"
        self.headers = get_headers(data_source='VCI')

    def _request_news(self, 
                      page=1, 
                      page_size=12,
                      start_date = None, 
                      end_date = None
                      )->dict:
        
        # Xử lý ngày tháng mặc định bên trong hàm để luôn lấy ngày hiện tại khi gọi
        if start_date is None:
            start_date = str(datetime.today().strftime('%Y-%m-%d'))
        if end_date is None:
            end_date = str(datetime.today().strftime('%Y-%m-%d'))

        params = {
            "page": page,
            "page_size": page_size, 
            "update_from": start_date, 
            "update_to": end_date,     
            "language": "vi",
            "ticker": "",
            "industry": "",
            "sentiment": "",
            "newsfrom": ""
        }
        response = requests.request("GET", url=self.url, headers=self.headers, params=params)
        # Lưu ý: Nếu request lỗi, dòng này sẽ crash script (theo yêu cầu không dùng try/except)
        response = response.json()
        return response

    def _fetch_and_filter_news(self, raw_meat: dict)->list:
        needed_keys = ['news_title', 'update_date', 'news_from_name', 'news_source_link']
        
        # Kiểm tra xem key 'news_info' có tồn tại không để tránh lỗi
        if 'news_info' not in raw_meat:
            return []

        filtered_list = [
            {key: item[key] for key in needed_keys if key in item}
            for item in raw_meat.get('news_info')
        ]
        return filtered_list

    def get_news(self):
        # Lấy 5 tin
        raw_data = self._request_news(page=1, page_size=5)
        return self._fetch_and_filter_news(raw_data)

# --- BOT SETUP ---
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True
# intents.members = True # Không cần thiết nếu chỉ chat trong channel
bot = commands.Bot(command_prefix='!', intents=intents)

# --- LOOP FUNCTION ---
# Sử dụng tasks.loop là cách chuẩn để chạy tác vụ lặp đi lặp lại trong Discord.py
@tasks.loop(seconds=MIN_WAIT_SECONDS)
async def news_loop():
    # 1. Lấy channel an toàn
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Không tìm thấy channel ID: {CHANNEL_ID}. Đang đợi cache...")
        return

    # 2. Lấy dữ liệu tin tức MỚI (phải gọi trong loop)
    # Instantiate class mỗi lần loop để đảm bảo header/time sạch sẽ
    news_tool = VCI_news()
    latest_news_data = news_tool.get_news()

    if not latest_news_data:
        print("Không lấy được tin hoặc API trả về rỗng.")
        return

    # 3. Lấy lịch sử tin nhắn để check trùng
    sent_links = set()
    # SỬA LỖI: Dùng async for cho history
    async for msg in channel.history(limit=HISTORY_LIMIT):
        sent_links.add(msg.content)

    # 4. So sánh và gửi
    # Dùng reversed để gửi tin cũ trước -> tin mới sau
    for item in reversed(latest_news_data):
        link = item['news_source_link']
        title = item['news_title']
        
        is_sent = False
        for content in sent_links:
            if link in content:
                is_sent = True
                break
        
        if not is_sent:
            print(f"--> Gửi tin: {title}")
            message_content = f"🔥 **{title}**\nNguồn: {item['news_from_name']}\n{link}"
            await channel.send(message_content)
        else:
            print(f"Bỏ qua tin cũ: {title}")
            pass

@news_loop.before_loop
async def before_news_loop():
    await bot.wait_until_ready() # Đợi bot đăng nhập xong mới chạy loop

@bot.event
async def on_ready():
    print(f"We are going in, {bot.user.name}")
    # Bắt đầu vòng lặp nếu chưa chạy
    if not news_loop.is_running():
        news_loop.start()

bot.run(token=token, log_handler=handler, log_level=logging.DEBUG)