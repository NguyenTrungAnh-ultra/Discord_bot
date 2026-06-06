import trafilatura
from playwright.sync_api import sync_playwright
import time
import requests
from src.core.scraper.browser import get_random_desktop_user_agent, DESKTOP_BROWSERS

def scrape_html(url):
    """Scrapes HTML content and converts to text using requests+trafilatura with Playwright fallback."""
    try:
        # Sử dụng requests với Session thay cho trafilatura.fetch_url
        session = requests.Session()
        user_agent = get_random_desktop_user_agent()
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Referer': 'https://google.com/'
        })
        
        content = None
        try:
            response = session.get(url, timeout=30)
            if response.status_code == 200:
                content = trafilatura.extract(response.text)
        except Exception as re_err:
            print(f"Requests fetch failed for {url}: {re_err}")
            
        # Nếu thất bại hoặc nội dung quá ngắn (trang rỗng do React/Vue render), dùng Playwright
        if not content or len(content.strip()) < 100:
            print(f"Content missing or too short, falling back to Playwright for: {url}")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                
                # Dùng User-Agent giả lập người dùng thật để tránh bị block
                playwright_user_agent = DESKTOP_BROWSERS["chrome"]["windows"]
                context = browser.new_context(user_agent=playwright_user_agent)
                page = context.new_page()
                
                try:
                    # Đổi sang domcontentloaded vì trang báo thường chứa Ads/Tracker chạy ngầm mãi không idle
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    # Đợi thêm một chút để chắc chắn nội dung Javascript đã render
                    time.sleep(3)
                    
                    html_content = page.content()
                    content = trafilatura.extract(html_content)
                except Exception as pe:
                    print(f"Playwright error for {url}: {pe}")
                finally:
                    context.close()
                    browser.close()
        
        return content
    except Exception as e:
        print(f"HTML scraping error for {url}: {e}")
        return None
