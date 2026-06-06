import os 
import json
from playwright.async_api import async_playwright
from src.core.scraper.browser import get_random_desktop_user_agent
import asyncio
import warnings


def clean_title(embed_title):
    if not embed_title: return ""
    # Thay thế icon và khoảng trắng thừa
    return embed_title.replace("🔥 ", "").strip()

async def get_article(link):
    print(f"--- Đang truy cập: {link} ---")
    tin_moi = "" # Mặc định là chuỗi rỗng để tránh lỗi NoneType
    
    # User Agent giả lập người dùng thật
    user_agent = get_random_desktop_user_agent()

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
