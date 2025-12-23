import time
import requests
from playwright.sync_api import sync_playwright

# Cấu hình
BOT_NAME = "VisionGuard"
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1453006532244672653/Bq1I65YZogrX37I4U0gqYWM6OLuO4Fhmo_KRTke9d02hjdqJZxHRPkG81AcpjMeR1yn6'

def send_to_discord(image_path, message):
    """Hàm gửi tin nhắn và file ảnh lên Discord"""
    try:
        with open(image_path, "rb") as f:
            payload = {"content": f"**[{BOT_NAME}]**: {message}"}
            files = {"file": (image_path, f, "image/png")}
            response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
            
        if response.status_code == 200 or response.status_code == 204:
            print(f"🚀 {BOT_NAME} đã gửi báo cáo lên Discord thành công!")
        else:
            print(f"❌ Lỗi gửi Discord: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Lỗi kết nối Webhook: {e}")

def run():
    TARGET_URL = "https://24hmoney.vn/indices?utm_medium=indices_leftside" # Thay bằng URL của bạn
    target_class = ".app-layout-main"  # Class bạn muốn chụp
    output_image = "./source/report_snapshot.png"

    with sync_playwright() as p:
        print(f"--- {BOT_NAME} đang khởi động ---")
        browser = p.chromium.launch(headless=True) # Để True để chạy ngầm
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        try:
            print(f"🔍 Đang quét mục tiêu: {TARGET_URL}")
            page.goto(TARGET_URL)

            # Đợi class xuất hiện
            element = page.locator(target_class).first
            element.wait_for(state="visible", timeout=30000)
            
            # Cuộn trang và nghỉ một chút để render hoàn toàn
            element.scroll_into_view_if_needed()
            time.sleep(2)

            # Chụp ảnh
            element.screenshot(path=output_image)
            print(f"📸 Đã chụp xong: {output_image}")

            # Gửi lên Discord
            send_to_discord(
                output_image, 
                f"Báo cáo thị trường đã sẵn sàng! Mục tiêu: `{target_class}`"
            )

        except Exception as e:
            error_msg = f"Đã xảy ra lỗi trong quá trình quét: {e}"
            print(f"❌ {error_msg}")
            # Có thể gửi thông báo lỗi lên Discord luôn
            # requests.post(DISCORD_WEBHOOK_URL, json={"content": f"⚠️ **{BOT_NAME} Error**: {error_msg}"})
        
        finally:
            browser.close()
            print(f"--- {BOT_NAME} đã hoàn thành nhiệm vụ và nghỉ ngơi ---")

if __name__ == "__main__":
    run()