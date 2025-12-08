import os
import requests
import json
from datetime import datetime, timedelta
from core.utils.user_agent import get_headers # Giữ lại import của bạn
import discord
from dotenv import load_dotenv

# --- CẤU HÌNH ---
HISTORY_FILE = "news_history.json" # Tên file lưu lịch sử
MAX_HISTORY_SIZE = 100 # Chỉ lưu 100 tin gần nhất để file không quá nặng

class VCI_news:
    def __init__(self):
        self.url = "https://ai.vietcap.com.vn/api/v2/news_info"
        self.headers = get_headers(data_source='VCI')

    def _request_news(self, page=1, page_size=12, start_date=None, end_date=None) -> dict:
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
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f'Request lỗi: {e}')
            return {}

    def _fetch_and_filter_news(self, raw_meat: dict) -> list:
        # QUAN TRỌNG: Phải lấy thêm trường 'id' để so sánh
        needed_keys = ['id', 'news_title', 'update_date', 'news_from_name', 'news_source_link']

        if not raw_meat or 'news_info' not in raw_meat:
            return []

        filtered_list = [
            {key: item[key] for key in needed_keys if key in item}
            for item in raw_meat.get('news_info', [])
        ]
        return filtered_list

    def get_news(self):
        # Lấy 12 tin mới nhất
        raw_data = self._request_news(page=1, page_size=12)
        return self._fetch_and_filter_news(raw_data)

# --- CÁC HÀM XỬ LÝ FILE JSON ---
def load_history():
    """Đọc file json lấy danh sách các ID đã gửi"""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Trả về danh sách ID (giả sử file lưu list các ID)
            return data
    except Exception as e:
        print(f"Lỗi đọc file history: {e}")
        return []

def save_history(id_list):
    """Lưu danh sách ID vào file json"""
    try:
        # Chỉ giữ lại MAX_HISTORY_SIZE ID mới nhất để file nhẹ
        trimmed_list = id_list[:MAX_HISTORY_SIZE]
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(trimmed_list, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu file history: {e}")

# --- MAIN ---
def main():
    load_dotenv()
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("Lỗi: Chưa cài đặt DISCORD_WEBHOOK_URL")
        # return # Uncomment return nếu muốn dừng script khi không có webhook

    # Khởi tạo webhook
    webhook = discord.SyncWebhook.from_url(webhook_url)
    
    # Lấy tin từ API
    news_tool = VCI_news()
    current_news_list = news_tool.get_news()
    
    if not current_news_list:
        print("Không lấy được dữ liệu từ API.")
        return

    # Lấy lịch sử ID đã gửi
    sent_ids = load_history()
    
    print(f"Đã lấy {len(current_news_list)} tin từ API. Lịch sử đang lưu {len(sent_ids)} tin.")

    count = 0
    # Tạo danh sách ID mới sẽ lưu lại (bắt đầu bằng danh sách cũ)
    updated_history = sent_ids.copy()
    
    # Duyệt ngược (reversed) để tin cũ nhất trong batch gửi trước, tin mới nhất gửi sau
    for item in reversed(current_news_list):
        news_id = item.get('id')
        
        # KIỂM TRA: Nếu ID chưa có trong danh sách đã gửi
        if news_id not in sent_ids:
            try:
                title = item.get('news_title', 'Không tiêu đề')
                link = item.get('news_source_link', '#')
                source = item.get('news_from_name', 'VCI')
                time_str = item.get('update_date')
                
                print(f"--> Gửi tin mới: {title}")
                
                # Gửi Webhook
                webhook.send(f"🔥 **{title}**\nNguồn: {source} ({time_str})\n{link}")
                
                # Đánh dấu là đã gửi bằng cách thêm vào danh sách temp (chèn vào đầu list để giữ tính mới nhất)
                updated_history.insert(0, news_id) 
                count += 1
                
            except Exception as e:
                print(f"Lỗi khi gửi tin: {e}")
        else:
            # print(f"Tin đã tồn tại, bỏ qua: {item.get('news_title')}")
            pass

    # Lưu lại trạng thái mới vào JSON
    if count > 0:
        save_history(updated_history)
        print(f"Đã gửi và lưu {count} tin mới.")
    else:
        print("Không có tin mới so với file lưu trữ.")

if __name__ == "__main__":
    main()