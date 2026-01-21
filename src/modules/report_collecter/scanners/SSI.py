"""
SSI Report Scraper
Scrapes financial reports from SSI website using Playwright
Website blocks HTTP requests (403) so requires browser automation
"""

import asyncio
import os
import pandas as pd
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import time
import random
import re


class Config:
    """Configuration for SSI scraper"""
    base_url = "https://www.ssi.com.vn"
    
    # SSI report sections (to be discovered during scraping)
    report_types = {
        "ban_tin_thi_truong": "/khach-hang-ca-nhan/ban-tin-thi-truong",
        "bao_cao_phan_tich": "/khach-hang-ca-nhan/bao-cao-phan-tich",
    }
    
    # Timeouts
    page_load_timeout = 30000
    element_timeout = 10000
    
    # Scraping limits
    max_pages_per_type = 10
    max_retries = 3
    retry_delay = 2


class SSIBaseScraper:
    """Base scraper with Playwright setup"""
    
    def __init__(self, headless: bool = True, slow_mo: int = 0):
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        
    async def __aenter__(self):
        await self.setup()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.teardown()
        
    async def setup(self):
        """Setup Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
    async def teardown(self):
        """Teardown Playwright browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def create_page(self) -> Page:
        """Create a new page"""
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        return await self.context.new_page()
        
    async def goto_with_retry(self, page: Page, url: str, retries: int = Config.max_retries) -> bool:
        """Navigate to URL with retry logic"""
        for attempt in range(retries):
            try:
                await page.goto(url, timeout=Config.page_load_timeout, wait_until='networkidle')
                return True
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(Config.retry_delay * (attempt + 1))
                else:
                    print(f"❌ Failed to load {url} after {retries} attempts")
                    return False
        return False


class SSIReportScraper(SSIBaseScraper):
    """Main scraper for SSI reports"""
    
    def __init__(self, headless: bool = True, slow_mo: int = 0):
        super().__init__(headless, slow_mo)
        self.base_dir = r".\temp\reports\SSI"
        
    def _get_report_dir(self, report_type: str) -> str:
        """Get directory for specific report type"""
        return os.path.join(self.base_dir, report_type)
        
    def _get_csv_path(self, report_type: str) -> str:
        """Get CSV file path"""
        report_dir = self._get_report_dir(report_type)
        return os.path.join(report_dir, "ssi_reports.csv")
        
    def _ensure_directories(self, report_type: str):
        """Ensure directories exist"""
        report_dir = self._get_report_dir(report_type)
        os.makedirs(report_dir, exist_ok=True)
        
    def _load_existing_reports(self, report_type: str) -> Tuple[pd.DataFrame, set]:
        """Load existing reports from CSV"""
        csv_path = self._get_csv_path(report_type)
        
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
                existing_ids = set(df['report_id'].tolist()) if 'report_id' in df.columns else set()
                print(f"📂 Loaded {len(df)} existing reports")
                return df, existing_ids
            except Exception as e:
                print(f"⚠️ Error loading CSV: {e}")
                return pd.DataFrame(), set()
        else:
            print("📝 No existing CSV found")
            return pd.DataFrame(), set()
            
    def _generate_report_id(self, title: str, url: str) -> str:
        """Generate unique report ID"""
        content = f"{title}|{url}"
        return hashlib.md5(content.encode()).hexdigest()
        
    def _save_reports(self, reports: List[Dict], report_type: str, old_df: pd.DataFrame):
        """Save reports to CSV"""
        csv_path = self._get_csv_path(report_type)
        
        if not reports:
            print("✨ No new reports to save")
            return
            
        new_df = pd.DataFrame(reports)
        
        if len(old_df) > 0:
            final_df = pd.concat([new_df, old_df], ignore_index=True)
            print(f"🎉 Added {len(new_df)} new reports. Total: {len(final_df)}")
        else:
            final_df = new_df
            print(f"🎉 Created new CSV with {len(final_df)} reports")
            
        final_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"💾 Saved to: {csv_path}")
        
    async def _wait_for_reports_loaded(self, page: Page) -> bool:
        """Wait for reports to load"""
        try:
            # Wait for common report container selectors
            # These will need to be adjusted based on actual SSI website structure
            selectors = [
                '.report-list',
                '.news-list', 
                '.article-list',
                'article',
                '[class*="report"]',
                '[class*="article"]'
            ]
            
            for selector in selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    print(f"✅ Found reports with selector: {selector}")
                    return True
                except:
                    continue
            
            print("⚠️ No report containers found with known selectors")
            return False
            
        except Exception as e:
            print(f"⚠️ Reports not loaded: {e}")
            return False
            
    async def _extract_reports_from_page(self, page: Page, report_type: str) -> List[Dict]:
        """Extract report information from page"""
        reports = []
        
        try:
            # Get page content for analysis
            content = await page.content()
            
            # Try to find all links that might be reports
            # SSI might use various patterns, so we'll be flexible
            links = await page.query_selector_all('a[href*="bao-cao"], a[href*="phan-tich"], a[href*="report"]')
            
            if not links:
                # Fallback: get all links and filter client-side
                links = await page.query_selector_all('a')
            
            print(f"📄 Found {len(links)} potential report links")
            
            for link in links:
                try:
                    href = await link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Filter for actual report links
                    if not any(keyword in href.lower() for keyword in ['bao-cao', 'phan-tich', 'report', 'analysis', 'tin-tuc']):
                        continue
                    
                    # Make full URL
                    if href.startswith('/'):
                        full_url = Config.base_url + href
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    # Extract title
                    title = await link.inner_text()
                    title = title.strip()
                    
                    if not title or len(title) < 10:  # Skip very short titles
                        continue
                    
                    # Extract date if visible near the link
                    date = ""
                    parent = await link.evaluate_handle('el => el.closest("div, article, li")')
                    if parent:
                        parent_text = await parent.inner_text()
                        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', parent_text)
                        if date_match:
                            date = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
                    
                    # Extract ticker if present
                    ticker = ""
                    ticker_match = re.search(r'\b([A-Z]{3,4})\b', title)
                    if ticker_match:
                        ticker = ticker_match.group(1)
                    
                    report = {
                        'report_id': '',
                        'report_type': report_type,
                        'title': title,
                        'ticker': ticker,
                        'industry': '',
                        'date': date,
                        'description': title,
                        'detail_url': full_url,
                        'pdf_url': '',
                        'download_url': '',
                        'downloaded': False,
                        'download_path': '',
                        'metadata': json.dumps({
                            'source': 'ssi_scraper',
                            'raw_title': title
                        })
                    }
                    
                    report['report_id'] = self._generate_report_id(title, full_url)
                    reports.append(report)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"❌ Error extracting reports: {e}")
            
        return reports
        
    async def scan_by_type(self, report_type: str, max_pages: int = Config.max_pages_per_type) -> Dict:
        """Scan reports by type"""
        print(f"\n{'='*60}")
        print(f"🔍 Scanning SSI: {report_type}")
        print(f"{'='*60}\n")
        
        self._ensure_directories(report_type)
        old_df, existing_ids = self._load_existing_reports(report_type)
        
        page = await self.create_page()
        all_reports = []
        
        try:
            # Get type URL
            type_url = Config.report_types.get(report_type, Config.report_types['ban_tin_thi_truong'])
            url = Config.base_url + type_url
            
            print(f"📄 Loading: {url}")
            
            if not await self.goto_with_retry(page, url):
                return {'report_type': report_type, 'total_reports': 0, 'reports': []}
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            # Wait for reports
            if not await self._wait_for_reports_loaded(page):
                print("⚠️ Could not detect report containers, will try to extract anyway")
            
            # Extract reports
            page_reports = await self._extract_reports_from_page(page, report_type)
            
            # Filter existing
            new_reports = [
                r for r in page_reports
                if r['report_id'] not in existing_ids
            ]
            
            print(f"✅ Found {len(new_reports)} new reports (total: {len(page_reports)})")
            all_reports = new_reports
            
        finally:
            await page.close()
        
        # Save reports
        self._save_reports(all_reports, report_type, old_df)
        
        return {
            'report_type': report_type,
            'total_reports': len(all_reports),
            'reports': all_reports
        }


async def scan_all(headless: bool = True) -> Dict:
    """Scan all report types"""
    async with SSIReportScraper(headless=headless) as scraper:
        results = {}
        
        for type_key in Config.report_types.keys():
            print(f"\n🔄 Processing: {type_key}")
            result = await scraper.scan_by_type(type_key)
            results[type_key] = result
            
        return results


async def scan_type_async(report_type: str, headless: bool = True) -> Dict:
    """Scan a single report type"""
    async with SSIReportScraper(headless=headless) as scraper:
        return await scraper.scan_by_type(report_type)


# Synchronous wrappers
def scan_type(report_type: str) -> Dict:
    """Synchronous wrapper"""
    return asyncio.run(scan_type_async(report_type))


def scan_all_sync() -> Dict:
    """Synchronous wrapper for scan_all"""
    return asyncio.run(scan_all())


if __name__ == "__main__":
    print("🚀 Testing SSI Scraper\n")
    
    # Test with visible browser to see what's happening
    result = asyncio.run(scan_type_async("ban_tin_thi_truong", headless=False))
    
    print(f"\n{'='*60}")
    print("📊 Results:")
    print(f"  Type: {result['report_type']}")
    print(f"  New reports: {result['total_reports']}")
    print(f"{'='*60}")
