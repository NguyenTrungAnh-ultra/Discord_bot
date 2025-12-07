import os
import requests
from datetime import datetime, timedelta
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
TIME_WINDOW_MINUTES = 10

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
        try:
            response = requests.request("GET", url=self.url, headers=self.headers, params=params)
        except:
            print('Request lỗi')
        response = response.json()
        return response

    def _fetch_and_filter_news(self, raw_meat: dict)->list:
        needed_keys = ['news_title', 'update_date', 'news_from_name', 'news_source_link']

        filtered_list = [
            {key: item[key] for key in needed_keys if key in item}
            for item in raw_meat.get('news_info')
        ]
        return filtered_list

    def get_news(self):
        raw_data = self._request_news(page=1, page_size=12)
        return self._fetch_and_filter_news(raw_data)

def main():
    # 1. Lấy Webhook URL từ biến môi trường (Cài trong GitHub Secrets sau)
    load_dotenv()
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("Lỗi: Chưa cài đặt DISCORD_WEBHOOK_URL")
        return

    # 2. Khởi tạo Webhook
    webhook = discord.SyncWebhook.from_url(webhook_url)
    
    # 3. Lấy tin tức
    news_tool = VCI_news()
    news_list = news_tool.get_news()
    
    print(f"Đã lấy được {len(news_list)} tin. Đang lọc tin mới trong {TIME_WINDOW_MINUTES} phút qua...")

    # 4. Xử lý logic thời gian
    # Lưu ý: Server GitHub dùng giờ UTC, VCI dùng giờ Việt Nam (GMT+7)
    # Ta sẽ chuyển giờ hiện tại của server + 7 tiếng để khớp với giờ Việt Nam
    now_vn = datetime.utcnow() + timedelta(hours=7)
    
    count = 0
    # Duyệt ngược để gửi tin cũ trước, tin mới sau
    for item in reversed(news_list):
        try:
            # Format của VCI: "2023-10-25 14:30:00"
            news_time_str = item.get('update_date')
            news_time = datetime.strptime(news_time_str, "%Y-%m-%d %H:%M:%S")
            
            # Tính khoảng cách thời gian
            time_diff = now_vn - news_time
            
            # Nếu tin tức xuất hiện trong khoảng thời gian đã định (TIME_WINDOW_MINUTES+1 phút)
            # time_diff.total_seconds() > 0 để tránh tin tương lai (nếu giờ server lệch)
            if 0 <= time_diff.total_seconds() <= (TIME_WINDOW_MINUTES * 60) + 21:
                
                title = item.get('news_title', 'Không tiêu đề')
                link = item.get('news_source_link', '#')
                source = item.get('news_from_name', 'VCI')

                print(f"--> Gửi tin: {title}")
                
                # Gửi qua Webhook
                webhook.send(f"🔥 **{title}**\nNguồn: {source} {news_time_str}\n{link}")
                count += 1
            else:
                print(f"Bỏ qua tin cũ lúc {news_time_str}")
                pass
                
        except Exception as e:
            print(f"Lỗi xử lý tin: {e}")

    if count == 0:
        print("Không có tin mới nào trong khung giờ này.")
    else:
        print(f"Đã gửi {count} tin.")

if __name__ == "__main__":
    main()