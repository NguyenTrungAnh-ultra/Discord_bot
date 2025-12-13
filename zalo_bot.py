import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles # <-- Thêm thư viện này để host ảnh
import requests
import json
import threading
from html2image import Html2Image
import os
from google import genai

# ================= CẤU HÌNH (ĐIỀN VÀO ĐÂY) =================
# 1. Token Zalo Bot
ZALO_BOT_TOKEN = os.environ.get('ZALO_TOKEN')

# 2. API Key Gemini
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# 3. Link Ngrok hiện tại của bạn (QUAN TRỌNG ĐỂ TẠO LINK ẢNH)
# Lưu ý: KHÔNG có dấu / ở cuối. Ví dụ: https://abc.ngrok-free.app
MY_NGROK_URL = "https://apogamous-racquel-adjacently.ngrok-free.dev" 

# Khởi tạo Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# Khởi tạo công cụ chụp ảnh
hti = Html2Image(output_path='.')
# ============================================================

app = FastAPI()

# --- 1. MỞ KHO ẢNH (QUAN TRỌNG) ---
# Dòng này cho phép Zalo truy cập vào thư mục hiện tại để lấy ảnh qua đường dẫn /images
app.mount("/images", StaticFiles(directory="."), name="images")

# --- 2. HÀM GỬI ẢNH ZALO (Theo tài liệu bạn gửi) ---
def send_zalo_photo(chat_id, photo_url, caption=""):
    url = f"https://bot-api.zaloplatforms.com/bot{ZALO_BOT_TOKEN}/sendPhoto"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "chat_id": chat_id,
        "photo": photo_url, # Link tuyệt đối
        "caption": caption
    }
    
    try:
        print(f"--> Đang gửi ảnh: {photo_url}")
        resp = requests.post(url, json=payload, headers=headers)
        print(f"--> Kết quả gửi ảnh: {resp.text}")
    except Exception as e:
        print(f"Lỗi gửi ảnh: {e}")

# --- 3. HÀM GỬI TEXT (Phụ trợ) ---
def send_zalo_text(chat_id, text):
    url = f"https://bot-api.zaloplatforms.com/bot{ZALO_BOT_TOKEN}/sendMessage"
    headers = {"Content-Type": "application/json"}
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload, headers=headers)

# --- 4. HÀM GEMINI TẠO HTML ---
def ask_gemini_to_gen_report(ticker):
    prompt = f"""
    Bạn là chuyên gia tài chính. Hãy tạo code HTML báo cáo cho mã {ticker}.
    Yêu cầu:
    - Width: 600px (quan trọng). Nền trắng.
    - Màu chủ đạo: #004d99 (Xanh Navy).
    - Có biểu đồ cột đơn giản (vẽ bằng CSS div).
    - Chỉ trả về code HTML, không markdown.
    """
    try:
        # Dùng model mà bạn đã check thành công (ví dụ gemini-1.5-flash)
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        if response.text:
            return response.text.replace("```html", "").replace("```", "").strip()
    except Exception as e:
        print(f"Lỗi Gemini: {e}")
    return None

# --- 5. LUỒNG XỬ LÝ CHÍNH ---
def process_request(chat_id, user_text):
    msg = user_text.lower()
    
    if "/summary_" in msg:
        try:
            ticker = user_text.split("_")[1].upper()
            send_zalo_text(chat_id, f"🔍 Đang vẽ báo cáo {ticker}...")
            
            # 1. Gemini viết Code HTML
            html_content = ask_gemini_to_gen_report(ticker)
            
            if html_content:
                # 2. Chụp ảnh lưu vào máy
                filename = f"report_{ticker}.png"
                # Xóa ảnh cũ nếu có để tránh lỗi cache
                if os.path.exists(filename):
                    os.remove(filename)
                    
                hti.screenshot(html_str=html_content, save_as=filename, size=(600, 800))
                
                # 3. Tạo Link Tuyệt Đối (Ngrok + Filename)
                # Đây là cái Zalo cần: https://ngrok.../images/report_FPT.png
                absolute_photo_url = f"{MY_NGROK_URL}/images/{filename}"
                
                # 4. Gửi ảnh cho khách
                send_zalo_photo(chat_id, absolute_photo_url, caption=f"Báo cáo {ticker}")
                
            else:
                send_zalo_text(chat_id, "Gemini không trả về nội dung.")
                
        except Exception as e:
            send_zalo_text(chat_id, f"Lỗi: {str(e)}")
            print(e)

# --- 6. WEBHOOK ---
@app.post("/zalo-webhook")
async def zalo_webhook(request: Request):
    try:
        data = await request.json()
        if 'message' in data and 'chat' in data['message']:
            chat_id = data['message']['chat']['id']
            if 'text' in data['message']:
                user_text = data['message']['text']
                threading.Thread(target=process_request, args=(chat_id, user_text)).start()
    except Exception:
        pass
    return {"status": "success"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)