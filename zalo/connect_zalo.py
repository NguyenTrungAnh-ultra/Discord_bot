import requests
import os

# --- CẤU HÌNH (ĐIỀN CẨN THẬN) ---

# 1. Bot Token: Lấy tại bot.zalo.me
# Lưu ý: Copy chính xác chuỗi ký tự, KHÔNG được có dấu cách thừa.
MY_BOT_TOKEN = os.environ.get('ZALO_TOKEN')

# 2. Webhook URL: Link Ngrok của bạn
# Lưu ý: Phải có https:// và đuôi /zalo-webhook (khớp với code main.py)
MY_WEBHOOK_URL = "https://apogamous-racquel-adjacently.ngrok-free.dev/zalo-webhook"

# 3. Secret Token: Tự đặt gì cũng được (Zalo bắt buộc phải có)
MY_SECRET_KEY = "123456789"

# ----------------------------------

# Tạo đường dẫn API chuẩn (Xóa bỏ các dấu < > nếu bạn lỡ copy nhầm)
api_endpoint = f"https://bot-api.zaloplatforms.com/bot{MY_BOT_TOKEN}/setWebhook"

payload = {
    "url": MY_WEBHOOK_URL,
    "secret_token": MY_SECRET_KEY
}

headers = {
    "Content-Type": "application/json"
}

print(f"--> Webhook URL: {MY_WEBHOOK_URL}")

try:
    response = requests.post(api_endpoint, json=payload, headers=headers)
    
    print("\n--- KẾT QUẢ TỪ ZALO ---")
    print("Status Code:", response.status_code)
    print("Phản hồi:", response.text)
    
    if response.status_code == 200 and '"error_code":0' in response.text:
        print("\n✅ THÀNH CÔNG! Bot đã kết nối với Code Python.")
    else:
        print("\n❌ THẤT BẠI. Hãy kiểm tra lại Token.")
        
except Exception as e:
    print(f"\n❌ Lỗi Code: {e}")