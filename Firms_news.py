import os
from News.tool import load_history, update_history
from News.tin_doanh_nghiep import VCI_news
from datetime import datetime
import discord
from dotenv import load_dotenv

# Config
HISTORY_FILE = "./source/requested_news.json" 
today = str(datetime.today().strftime('%Y-%m-%d'))

def main():
    load_dotenv()
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("Lỗi: Chưa cài đặt DISCORD_WEBHOOK_URL")

    # Khởi tạo webhook
    webhook = discord.SyncWebhook.from_url(webhook_url)
    #############################################################################################################
    # Lấy tin từ API
    news_tool = VCI_news()
    current_news_list = news_tool.get_news(page=1, page_size=50)
    
    if not current_news_list:
        print("Không lấy được dữ liệu từ API.")
        return

    # Lấy lịch sử đã gửi
    sent_ids = load_history(direct=HISTORY_FILE)
    
    print(f"Đã lấy {len(current_news_list)} tin từ API. Lịch sử đang lưu {len(sent_ids)} tin.")

    count = 0
    # Tạo danh sách mới sẽ lưu lại (bắt đầu bằng danh sách cũ)
    updated_history = sent_ids.copy()
    
    # Duyệt ngược (reversed) để tin cũ nhất trong batch gửi trước, tin mới nhất gửi sau
    for item in reversed(current_news_list):
        # KIỂM TRA: Nếu tin chưa có trong danh sách đã gửi
        if item not in sent_ids:
            try:
                title = item.get('news_title', 'Không tiêu đề')
                link = item.get('news_source_link', '#')
                source = item.get('news_from_name', 'VCI')
                time_str = item.get('update_date')
                
                print(f"--> Gửi tin mới: {title}")
                
                # Gửi Webhook
                webhook.send(f"🔥 **{title}**\nNguồn: {source} ({time_str})\n{link}") ######################################
                # print(f"🔥 **{title}**\nNguồn: {source} ({time_str})\n{link}")
                
                # Đánh dấu là đã gửi bằng cách thêm vào danh sách temp (chèn vào đầu list để giữ tính mới nhất)
                updated_history.insert(0, item) 
                count += 1
                
            except Exception as e:
                print(f"Lỗi khi gửi tin: {e}")
        else:
            # print(f"Tin đã tồn tại, bỏ qua: {item.get('news_title')}")
            pass

    # Lưu lại trạng thái mới vào JSON
    if count > 0:
        update_history(_list = updated_history, direct=HISTORY_FILE)
        print(f"Đã gửi và lưu {count} tin mới.")
    else:
        print("Không có tin mới so với file lưu trữ.")

if __name__ == "__main__":
    main()