from src.utils.browser_profiles import browser
import asyncio
from playwright.async_api import async_playwright

class Config:
    toan_canh_thi_truong_url = "https://www.abs.vn/phan-tich-dau-tu/trung-tam-phan-tich/toan-canh-thi-truong/"
    bao_cao_cong_ty_url = "https://www.abs.vn/phan-tich-dau-tu/trung-tam-phan-tich/bao-cao-cong-ty/"
    bao_cao_nganh_url = "https://www.abs.vn/phan-tich-dau-tu/trung-tam-phan-tich/bao-cao-nganh"
    bao_cao_vimochienluoc_url = "https://www.abs.vn/phan-tich-dau-tu/trung-tam-phan-tich/bao-cao-vi-mo-va-chien-luoc/"

async def run(toan_canh_thi_truong_url=False, 
                bao_cao_cong_ty_url=False, 
                bao_cao_nganh_url=False,
                bao_cao_vimochienluoc_url=False):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(f"{Config.bao_cao_cong_ty_url}")
        asyncio.time.sleep(2)
        
        






        await browser.close()


