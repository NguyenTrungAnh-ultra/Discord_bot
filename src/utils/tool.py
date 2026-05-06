import os 
import json
from playwright.async_api import async_playwright
from src.utils.user_agent import get_random_desktop_user_agent
import asyncio
import time
import warnings


def load_history(direct:str)->list:
    """Đọc file json lấy danh sách tin đã gửi (DEPRECATED: Use Database instead)"""
    warnings.warn("load_history is deprecated, use src.core.db instead", DeprecationWarning, stacklevel=2)
    if not os.path.exists(direct):
        return []
    try:
        with open(direct, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Lỗi đọc file history: {e}")
        return []

def save_history(_list:list, direct:str, 
                 MAX_SIZE:int = 50_000
                 ):
    """Lưu danh sách vào file json"""
    try:
        trimmed_list = _list[:MAX_SIZE]
        # Save
        with open(direct, 'w', encoding='utf-8') as f:
            json.dump(trimmed_list, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi lưu file history: {e}")

def update_history(_list:list, 
                   direct:str
                   ):
    # 1. Load dữ liệu cũ
    existing_data = []
    if os.path.exists(direct):
        try:
            with open(direct, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            existing_data = []

    # 2. Tạo tập hợp các ID đã tồn tại để kiểm tra cho nhanh (O(1))
    # Giả sử key định danh là 'id', nếu không có 'id' thì đổi thành 'news_title'
    existing_ids = {item.get('id') for item in existing_data}

    count_added = 0
    
    # 3. Duyệt danh sách mới, chỉ thêm cái nào chưa có ID trong file cũ
    for item in _list:
        item_id = item.get('id')
        
        # Chỉ thêm nếu có ID và ID đó chưa từng xuất hiện
        if item_id and item_id not in existing_ids:
            existing_data.append(item)
            existing_ids.add(item_id) # Cập nhật luôn vào set để tránh trùng lặp nội bộ
            count_added += 1

    # 4. Lưu lại toàn bộ (Cũ + Mới thêm) vào file
    if count_added > 0:
        with open(direct, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        print(f"Đã lưu thêm {count_added} tin mới vào {direct}.")
    else:
        print("Không có tin mới cần lưu (tất cả đã tồn tại trong file).")

def clean_title(embed_title):
    if not embed_title: return ""
    # Thay thế icon và khoảng trắng thừa
    return embed_title.replace("🔥 ", "").strip()

async def get_artical(link):
    print(f"--- Đang truy cập: {link} ---")
    tin_moi = "" # Mặc định là chuỗi rỗng để tránh lỗi NoneType
    
    # User Agent giả lập người dùng thật
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                    '--no-first-run',
                    '--no-zygote'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=user_agent
            )
            page = await context.new_page()
            
            # Tăng timeout lên để tránh mạng lag
            page.set_default_navigation_timeout(30000)
            page.set_default_timeout(30000)

            await page.goto(link)

            # 1. Chờ thẻ .content xuất hiện
            print("⏳ Đang chờ nội dung...")
            try:
                await page.wait_for_selector(".content", timeout=15000)
            except:
                print("⚠️ Không tìm thấy class .content, thử lấy body...")
                # Fallback: Nếu không có .content thì lấy toàn bộ body (phòng hờ)
                await page.wait_for_selector("body", timeout=15000)

            # 2. Cuộn trang để kích hoạt load ảnh/text nếu web dùng lazy load
            # (Quan trọng để lấy đủ nội dung dài)
            for _ in range(3):
                await page.mouse.wheel(0, 2000)
                await asyncio.sleep(0.5)

            # 3. Lấy nội dung
            tin_moi = await page.locator(".content").inner_text()

            print(f"✅ Đã lấy được {len(tin_moi)} ký tự.")

        except Exception as e:
            print(f"❌ Lỗi Playwright: {e}")
        finally:
            await browser.close()
    
    return tin_moi

# if __name__ == '__main__':
#     art = get_artical('https://trading.vietcap.com.vn/ai-news/post-detail/hnm-bien-tai-hanoimilk-con-gai-chu-tich-lien-tuc-mua-ban-co-phieu?language=vi')
#     print(art)