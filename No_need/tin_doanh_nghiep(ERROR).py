import json
from bs4 import BeautifulSoup
from .config import BASE_URL, NEWS_URL, DATA_FILE
from core.utils.user_agent import get_random_desktop_user_agent
from playwright.sync_api import sync_playwright
import os
import random
import time

def load_data():
    """
    Kiểm tra xem có đã có data trước đó chưa và thực hiện Incremental Scraping.
    """

    article_links = []
    existing_urls = set()

    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                article_links = json.load(f)
                for item in article_links:
                    existing_urls.add(item['link'])
            print(f"📚 Đã tải {len(article_links)} bài viết cũ.")
        except Exception:
            article_links = []

    return article_links, existing_urls

def extract_news(html_content:str,
                 existing_urls:set,
                 article_links:list
                 ):
    soup = BeautifulSoup(html_content, 'html.parser')
    cards = soup.select(".mantine-Card-root")
    print(f"\n✅ Tìm thấy {len(cards)} thẻ tin tức.\n")

    new_count = 0
    fresh = []
    for card in cards:
        # Logic tìm thẻ a (giữ nguyên của bạn)
        # Lưu ý: Đôi khi href không chứa full domain, code bạn đã xử lý tốt đoạn này
        link_tag = card.find("a", href=True) 
        
        # Lọc link kỹ hơn để tránh lấy nhầm link rác
        if link_tag and "/ai-news/post-detail" in link_tag['href']:
            relative_link = link_tag['href']
            full_link = BASE_URL + relative_link if not relative_link.startswith("http") else relative_link

            # HTML Vietcap dùng .mantine-Title-root cho tiêu đề
            # Các thẻ .mantine-Text-root thường là nhãn (Tích cực/Tiêu cực) nên phải để sau hoặc bỏ qua
            title_tag = card.select_one(".mantine-Title-root")
            
            if not title_tag:
                    # Fallback: Nếu không thấy class chuẩn thì mới tìm thẻ h1, h2
                    title_tag = card.select_one("h1, h2, h3")
                    
            title = title_tag.get_text(strip=True) if title_tag else "Không tiêu đề"

            if full_link not in existing_urls:
                print(f"🔥 TIN MỚI: {title}")
                fresh.append({
                    "title": title,
                    "link": full_link
                })
                existing_urls.add(full_link)
                new_count += 1
    # update tin moi
    article_links = fresh+article_links

    if new_count > 0:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(article_links, f, ensure_ascii=False, indent=4)
        print(f"\n🎉 Đã cập nhật {new_count} bài. Tổng: {len(article_links)}")
        return fresh
    else:
        print(f"\n💤 Không có bài mới.")
        return False

def run():
    article_links, existing_urls = load_data()

    MAX_RETRIES = 3
    tin_moi = None
    for attempt in range(MAX_RETRIES):
        try: #chữa lỗi cold start của MacOS
            user_agent  = get_random_desktop_user_agent()
            with sync_playwright() as p:

                print("🚀 Đang khởi động trình duyệt...")
                launch_args = [
                        '--disable-gpu',            # Tắt GPU hardware acceleration (nguyên nhân crash số 1)
                        '--no-sandbox',             # Tắt sandbox (giúp tránh lỗi quyền hạn)
                        '--disable-dev-shm-usage',  # Khắc phục lỗi thiếu bộ nhớ shared memory
                        '--disable-setuid-sandbox',
                        '--no-first-run',
                        '--no-zygote'
                    ]
                browser = p.chromium.launch(headless=True,
                                            args= launch_args
                                            )

                # --- Cấu hình Viewport & User Agent ---
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080}, # Bắt buộc mở rộng màn hình
                    user_agent= user_agent
                )
                page = context.new_page()
                page.set_default_navigation_timeout(60000) 
                page.set_default_timeout(60000)

                print(f"--- Đang truy cập: {NEWS_URL} ---")
                page.goto(NEWS_URL)

                try:
                    print("⏳ Đang chờ dữ liệu tải về...")
                    
                    # Chờ ít nhất một thẻ card xuất hiện (timeout 15s)
                    # Điều này đảm bảo HTML đã được JS render xong
                    page.wait_for_selector(".mantine-Card-root", timeout=15000)
                    
                    # Cuộn trang để kích hoạt Lazy Load (nếu có)
                    for i in range(3):
                        print(f"⬇️ Đang cuộn trang lần {i+1}...")
                        page.mouse.wheel(0, 3000) # Cuộn mạnh hơn chút
                        time.sleep(2) # Chờ nội dung mới render sau khi cuộn

                    # Lấy HTML
                    html_content = page.content()
                    tin_moi = extract_news(html_content=html_content, existing_urls=existing_urls, article_links=article_links)

                except Exception as e:
                    print(f"❌ Lỗi: {e}")
                    # Chụp ảnh lỗi để debug
                    page.screenshot(path="/Users/nguyentrunganhonichan/Documents/Discord_bot/News/debug_error.png")
                finally:
                    browser.close()
                    break
        except:
            continue
    return tin_moi

if __name__ == "__main__":
    run()