from playwright.sync_api import sync_playwright
import time

def run():
    # Sử dụng 'with' để tự động đóng trình duyệt khi xong việc
    with sync_playwright() as p:
        # 1. Khởi động trình duyệt
        # headless=False nghĩa là CÓ hiện cửa sổ trình duyệt để bạn theo dõi
        # Nếu muốn chạy ngầm (không hiện cửa sổ), sửa thành True
        browser = p.chromium.launch(headless=True)
        
        # 2. Tạo một ngữ cảnh (context) mới
        # Giả lập kích thước màn hình và User Agent thực tế để tránh bị chặn
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
        )
        page = context.new_page()

        print("--- Đang truy cập Vietcap ---")
        page.goto("https://trading.vietcap.com.vn/ai-news/market")

        # 3. Chờ đợi thông minh
        # Trang này là SPA (Single Page App), cần chờ request mạng tải xong dữ liệu
        try:
            print("--- Đang chờ tải dữ liệu ---")
            page.wait_for_load_state("networkidle", timeout=10000) # Chờ đến khi mạng rảnh (tối đa 10s)
        except:
            print("Cảnh báo: Hết thời gian chờ mạng, nhưng vẫn tiếp tục...")

        # Chờ thêm 2 giây để chắc chắn giao diện (UI) đã vẽ xong
        time.sleep(2)

        # 4. Lấy dữ liệu (Ví dụ: Lấy tiêu đề trang)
        title = page.title()
        print(f"Tiêu đề trang web: {title}")

        # 5. Chụp ảnh màn hình lưu lại
        content = page.content()
        print(content)

        # Đóng trình duyệt
        browser.close()

if __name__ == "__main__":
    run()