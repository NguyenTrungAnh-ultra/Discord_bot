"""
VCBS Report Scraper
Scrapes financial reports from VCBS website using Playwright
Supports 6 report types with search by ticker/industry
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


class Config:
    """Configuration for VCBS scraper"""
    base_url = "https://www.vcbs.com.vn/trung-tam-phan-tich"
    
    report_types = {
        "bao_cao_vi_mo": "BCVM",
        "bao_cao_doanh_nghiep": "BCDN",
        "bao_cao_nganh": "BCN",
        "bao_cao_chung_khoan_phai_sinh": "BCPS",
        "bao_cao_thi_truong": "BCTT",
        "bao_cao_trai_phieu": "BCTP"
    }
    
    report_type_names = {
        "BCVM": "Báo cáo vĩ mô",
        "BCDN": "Báo cáo doanh nghiệp",
        "BCN": "Báo cáo ngành",
        "BCPS": "Báo cáo chứng khoán phái sinh",
        "BCTT": "Báo cáo thị trường",
        "BCTP": "Báo cáo trái phiếu"
    }
    
    # Timeouts
    page_load_timeout = 30000  # 30 seconds
    element_timeout = 10000    # 10 seconds
    
    # Scraping limits
    max_pages_per_type = 10
    max_retries = 3
    retry_delay = 2  # seconds


class VCBSBaseScraper:
    """Base scraper class with Playwright setup/teardown"""
    
    def __init__(self, headless: bool = True, slow_mo: int = 0):
        """
        Initialize base scraper
        
        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down operations by specified milliseconds
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.setup()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
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
        """Create a new page in the browser context"""
        if not self.context:
            raise RuntimeError("Browser context not initialized. Call setup() first.")
        return await self.context.new_page()
        
    async def goto_with_retry(self, page: Page, url: str, retries: int = Config.max_retries) -> bool:
        """
        Navigate to URL with retry logic
        
        Args:
            page: Playwright page object
            url: URL to navigate to
            retries: Number of retries
            
        Returns:
            True if successful, False otherwise
        """
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


class VCBSReportScraper(VCBSBaseScraper):
    """Main scraper for VCBS reports"""
    
    def __init__(self, headless: bool = True, slow_mo: int = 0):
        super().__init__(headless, slow_mo)
        self.base_dir = r".\temp\reports\VCBS"
        
    def _get_report_dir(self, report_type: str) -> str:
        """Get directory for specific report type"""
        type_name = list(Config.report_types.keys())[
            list(Config.report_types.values()).index(report_type)
        ]
        return os.path.join(self.base_dir, type_name)
        
    def _get_csv_path(self, report_type: str) -> str:
        """Get CSV file path for specific report type"""
        report_dir = self._get_report_dir(report_type)
        return os.path.join(report_dir, "vcbs_reports.csv")
        
    def _ensure_directories(self, report_type: str):
        """Ensure report directories exist"""
        report_dir = self._get_report_dir(report_type)
        os.makedirs(report_dir, exist_ok=True)
        
    def _load_existing_reports(self, report_type: str) -> Tuple[pd.DataFrame, set]:
        """
        Load existing reports from CSV
        
        Returns:
            Tuple of (DataFrame, set of report_ids)
        """
        csv_path = self._get_csv_path(report_type)
        
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
                existing_ids = set(df['report_id'].tolist()) if 'report_id' in df.columns else set()
                print(f"📂 Loaded {len(df)} existing reports from CSV")
                return df, existing_ids
            except Exception as e:
                print(f"⚠️ Error loading CSV: {e}")
                return pd.DataFrame(), set()
        else:
            print("📝 No existing CSV found, will create new one")
            return pd.DataFrame(), set()
            
    def _generate_report_id(self, title: str, pdf_url: str) -> str:
        """Generate unique report ID from title and URL"""
        content = f"{title}|{pdf_url}"
        return hashlib.md5(content.encode()).hexdigest()
        
    def _save_reports(self, reports: List[Dict], report_type: str, old_df: pd.DataFrame):
        """
        Save reports to CSV
        
        Args:
            reports: List of new reports
            report_type: Type of report
            old_df: Existing DataFrame
        """
        csv_path = self._get_csv_path(report_type)
        
        if not reports:
            print("✨ No new reports to save")
            return
            
        new_df = pd.DataFrame(reports)
        
        # Combine with old data
        if len(old_df) > 0:
            final_df = pd.concat([new_df, old_df], ignore_index=True)
            print(f"🎉 Added {len(new_df)} new reports. Total: {len(final_df)}")
        else:
            final_df = new_df
            print(f"🎉 Created new CSV with {len(final_df)} reports")
            
        # Save to CSV
        final_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"💾 Saved to: {csv_path}")
        
    async def _wait_for_reports_loaded(self, page: Page) -> bool:
        """
        Wait for report cards to load
        
        Returns:
            True if loaded successfully
        """
        try:
            # Wait for report list container
            await page.wait_for_selector('.t-acReportList_list', timeout=Config.element_timeout)
            
            # Wait for at least one report card
            await page.wait_for_selector('.t-acReportList_list-item', timeout=Config.element_timeout)
            
            # Small delay to ensure all cards are rendered
            await asyncio.sleep(0.5)
            
            return True
        except Exception as e:
            print(f"⚠️ Reports not loaded: {e}")
            return False
            
    async def _extract_reports_from_page(self, page: Page, report_type: str) -> List[Dict]:
        """
        Extract report information from current page with improved PDF extraction
        """
        reports = []
        
        try:
            cards = await page.query_selector_all('.o-simpleReportCard')
            print(f"📄 Found {len(cards)} report cards on page")
            
            for idx, card in enumerate(cards):
                try:
                    title_elem = await card.query_selector('.o-simpleReportCard_title h3')
                    title_text = await title_elem.inner_text() if title_elem else ""
                    
                    desc_elem = await card.query_selector('.o-simpleReportCard_description p')
                    description = await desc_elem.inner_text() if desc_elem else ""
                    
                    # Extract ticker from title if BCDN
                    ticker = ""
                    if report_type == 'BCDN' and title_text:
                        parts = title_text.split('-', 1)
                        if len(parts) > 0:
                            ticker = parts[0].strip()
                    
                    # Extract date from description
                    import re
                    date = ""
                    date_match = re.search(r'(\d{2})[./](\d{2})[./](\d{4})', description)
                    if date_match:
                        date = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
                    
                    report = {
                        'report_id': '',
                        'report_type': report_type,
                        'title': title_text.strip(),
                        'ticker': ticker,
                        'industry': '',
                        'date': date,
                        'description': description.strip(),
                        'pdf_url': '',
                        'download_url': '',
                        'downloaded': False,
                        'download_path': ''
                        })
                    }
                    
                    report['report_id'] = self._generate_report_id(
                        report['title'],
                        report.get('pdf_url', report['description'])
                    )
                    
                    reports.append(report)
                    
                except Exception as e:
                    print(f"⚠️ Error extracting card {idx}: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error extracting reports: {e}")
            
        return reports
        
    async def scan_by_type(self, report_type: str, max_pages: int = Config.max_pages_per_type) -> Dict:
        """
        Scan reports by type
        
        Args:
            report_type: Report type code (BCVM, BCDN, etc.)
            max_pages: Maximum pages to scrape
            
        Returns:
            Dictionary with scan results
        """
        print(f"\n{'='*60}")
        print(f"🔍 Scanning: {Config.report_type_names.get(report_type, report_type)}")
        print(f"{'='*60}\n")
        
        # Ensure directories exist
        self._ensure_directories(report_type)
        
        # Load existing reports
        old_df, existing_ids = self._load_existing_reports(report_type)
        
        # Create page
        page = await self.create_page()
        
        all_reports = []
        page_num = 1
        found_existing = False
        
        try:
            while page_num <= max_pages:
                # Construct URL
                if page_num == 1:
                    url = f"{Config.base_url}?code={report_type}"
                else:
                    url = f"{Config.base_url}?code={report_type}&page={page_num}"
                    
                print(f"📄 Scraping page {page_num}: {url}")
                
                # Navigate to page
                if not await self.goto_with_retry(page, url):
                    break
                    
                # Wait for reports to load
                if not await self._wait_for_reports_loaded(page):
                    print(f"⚠️ No reports found on page {page_num}, stopping")
                    break
                    
                # Extract reports
                page_reports = await self._extract_reports_from_page(page, report_type)
                
                # Filter out existing reports
                new_reports = [
                    r for r in page_reports 
                    if r['report_id'] not in existing_ids
                ]
                
                print(f"✅ Found {len(new_reports)} new reports (total: {len(page_reports)})")
                
                if len(new_reports) == 0:
                    found_existing = True
                    print("🛑 All reports on this page already exist, stopping")
                    break
                    
                all_reports.extend(new_reports)
                
                # Check if there's a next page
                next_button = await page.query_selector('a.link-next:not(.disabled)')
                if not next_button:
                    print("📍 Reached last page")
                    break
                    
                page_num += 1
                
                # Small delay between pages
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
        finally:
            await page.close()
            
        # Save reports
        self._save_reports(all_reports, report_type, old_df)
        
        return {
            'report_type': report_type,
            'total_reports': len(all_reports),
            'pages_scraped': page_num,
            'reports': all_reports
        }


async def scan_all_reports(headless: bool = True) -> Dict:
    """
    Scan all report types
    
    Args:
        headless: Run in headless mode
        
    Returns:
        Dictionary with results for all types
    """
    async with VCBSReportScraper(headless=headless) as scraper:
        results = {}
        
        for type_key, type_code in Config.report_types.items():
            print(f"\n🔄 Processing: {type_key}")
            result = await scraper.scan_by_type(type_code)
            results[type_key] = result
            
        return results


async def scan_by_type_standalone(report_type: str, headless: bool = True) -> Dict:
    """
    Scan a single report type (standalone function)
    
    Args:
        report_type: Report type code or key
        headless: Run in headless mode
        
    Returns:
        Dictionary with scan results
    """
    # Convert key to code if necessary
    if report_type in Config.report_types:
        report_type = Config.report_types[report_type]
        
    async with VCBSReportScraper(headless=headless) as scraper:
        return await scraper.scan_by_type(report_type)



# Synchronous wrappers for easy usage
def scan_all() -> Dict:
    """Synchronous wrapper for scan_all_reports"""
    return asyncio.run(scan_all_reports())


def scan_type(report_type: str) -> Dict:
    """Synchronous wrapper for scan_by_type_standalone"""
    return asyncio.run(scan_by_type_standalone(report_type))


def scan_ticker(ticker: str) -> Dict:
    """
    Scan reports for specific ticker (convenience function)
    
    Args:
        ticker: Stock ticker code (e.g., 'VNM')
        
    Returns:
        Dictionary with scan results including filtered reports
    """
    # This is a simplified version - just scan BCDN and filter by ticker
    result = scan_type('bao_cao_doanh_nghiep')
    
    # Filter reports by ticker
    ticker = ticker.upper()
    filtered_reports = [
        r for r in result.get('reports', [])
        if ticker in r.get('ticker', '').upper() or ticker in r.get('title', '').upper()
    ]
    
    return {
        'ticker': ticker,
        'report_type': 'BCDN',
        'total_reports': len(filtered_reports),
        'reports': filtered_reports
    }


def scan_industry(industry: str) -> Dict:
    """
    Scan reports for specific industry (convenience function)
    
    Args:
        industry: Industry name
        
    Returns:
        Dictionary with scan results including filtered reports
    """
    # Scan BCN and filter by industry keyword
    result = scan_type('bao_cao_nganh')
    
    # Filter reports by industry in title/description
    filtered_reports = [
        r for r in result.get('reports', [])
        if industry.lower() in r.get('title', '').lower() or 
           industry.lower() in r.get('description', '').lower()
    ]
    
    # Set industry field
    for r in filtered_reports:
        r['industry'] = industry
    
    return {
        'industry': industry,
        'report_type': 'BCN',
        'total_reports': len(filtered_reports),
        'reports': filtered_reports
    }



if __name__ == "__main__":
    # Test the scraper
    print("🚀 Testing VCBS Scraper\n")
    
    # Test scanning one type
    result = scan_type("bao_cao_doanh_nghiep")
    
    print(f"\n{'='*60}")
    print("📊 Results:")
    print(f"  Type: {result['report_type']}")
    print(f"  New reports: {result['total_reports']}")
    print(f"  Pages scraped: {result['pages_scraped']}")
    print(f"{'='*60}")
