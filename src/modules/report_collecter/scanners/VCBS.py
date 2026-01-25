"""
VCBS Report Scraper (Playwright Version)
Scrapes financial reports from VCBS website using Playwright.
Handles dynamic buttons (click to get link).
"""

import asyncio
import os
import pandas as pd
import hashlib
import re
import requests
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

class Config:
    """Configuration for VCBS scraper"""
    base_url = "https://www.vcbs.com.vn/trung-tam-phan-tich"
    
    # Report types map
    report_types = {
        "bao_cao_doanh_nghiep": "BCDN",
        "bao_cao_nganh": "BCN",
    }
    
    report_type_names = {
        "BCDN": "Báo cáo doanh nghiệp",
        "BCN": "Báo cáo ngành",
    }
    
    # Selectors
    SELECTORS = {
        'list_item': '.t-acReportList_list-item',
        'ticker': '.o-simpleReportCard_title',
        'title': '.o-simpleReportCard_description',
        'button': '.o-simpleReportCard_button-hideButton',
        'next_page': 'button.pagination-next', # Adjust if needed based on site
        'disabled_next': 'button.pagination-next[disabled]'
    }
    
    # Timeouts
    page_load_timeout = 60000 
    element_timeout = 5000
    
    # Limits
    max_pages = 5 # Scan latest 5 pages by default to be safe

def extract_tickers(title: str) -> Optional[str]:
    """Exclusion list based ticker extraction"""
    excluded = {
        'CTCP', 'TCT', 'TNHH', 'VCBS', 'BCDN', 'BCN', 'MUA', 'BAN',
        'VND', 'USD', 'EUR', 'PDF', 'FY', 'YTD', 'TTM', 'EPS', 'ROE', 'ROA',
        'ABB', 'CEO', 'CFO', 'COO', 'KBSV', 'TMCP', 'NGAN', 'HANG', 'CONG', 'TY',
        'LNST', 'SVCK', 'THU', 'GIAO', 'CHUY', 'HSX', 'HNX', 'UPCOM', 'VNIND',
        'VNI', 'VN30', 'TRU', 'TANG', 'GIAM', 'LOI', 'NHUAN', 'DOANH', 'THUE',
        'QUY', 'NAM', 'THANG', 'TUAN', 'NGAY', 'KHONG', 'DANH', 'GIA', 'TRIEN', 'VONG'
    }
    
    # Regex: Look for 3-4 uppercase letters, ensure boundaries are not alphanumeric
    # Also handle underscores like _VCG_
    tickers = re.findall(r'(?<![A-Za-z0-9])([A-Z]{3,4})(?![A-Za-z0-9])', title.upper())
    tickers = [t for t in tickers if t not in excluded]
    unique_tickers = sorted(set(tickers))
    
    if unique_tickers:
        return ','.join(unique_tickers)
    return None

class VCBSScanner:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_dir = os.path.join(os.getcwd(), "temp", "reports", "VCBS")
        
    def _get_paths(self, report_type_code: str) -> Tuple[str, str]:
        """Get output directory and CSV path"""
        # Map code back to directory name
        dir_name = "bao_cao_doanh_nghiep" if report_type_code == "BCDN" else "bao_cao_nganh"
        out_dir = os.path.join(self.base_dir, dir_name)
        os.makedirs(out_dir, exist_ok=True)
        return out_dir, os.path.join(out_dir, "vcbs_reports.csv")

    def _load_existing(self, csv_path: str) -> set:
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
                if 'report_id' in df.columns:
                    return set(df['report_id'].astype(str).tolist())
            except:
                pass
        return set()

    def _save_reports(self, reports: List[Dict], csv_path: str):
        if not reports:
            return
            
        new_df = pd.DataFrame(reports)
        
        if os.path.exists(csv_path):
            try:
                old_df = pd.read_csv(csv_path, encoding='utf-8-sig')
                combined = pd.concat([new_df, old_df], ignore_index=True)
                # Deduplicate by ID, keeping new ones (top)
                combined.drop_duplicates(subset='report_id', keep='first', inplace=True)
                combined.to_csv(csv_path, index=False, encoding='utf-8-sig')
            except Exception as e:
                print(f"⚠️ Merge error: {e}, overwriting")
                new_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        else:
            new_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
        print(f"💾 Saved {len(reports)} reports to {csv_path}")

    def scan_type(self, type_code: str, max_pages: int = Config.max_pages):
        print(f"\n🚀 Scanning VCBS: {Config.report_type_names.get(type_code, type_code)}")
        out_dir, csv_path = self._get_paths(type_code)
        existing_ids = self._load_existing(csv_path)
        
        new_reports = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()
            
            # Navigate
            url = f"{Config.base_url}?code={type_code}"
            print(f"📄 Navigating to: {url}")
            try:
                page.goto(url, timeout=60000, wait_until='networkidle')
            except Exception as e:
                print(f"❌ Failed to load page: {e}")
                browser.close()
                return
            
            # Pagination loop
            current_page = 1
            while current_page <= max_pages:
                print(f"📄 Processing Page {current_page}...")
                
                # Wait for list load
                try:
                    page.wait_for_selector(Config.SELECTORS['list_item'], timeout=10000)
                except:
                    print("⚠️ No reports found (selector timeout).")
                    break
                
                items = page.query_selector_all(Config.SELECTORS['list_item'])
                print(f"   Found {len(items)} items.")
                
                page_new_count = 0
                
                for item in items:
                    try:
                        # Extract Basic Info
                        title_el = item.query_selector(Config.SELECTORS['title'])
                        
                        # Note: The structure description said 'description' contains title, 
                        # 'title' contains ticker. Adjusting based on user request details:
                        # - o-simpleReportCard_title -> ticker (sometimes title if no ticker?)
                        # - o-simpleReportCard_description -> title
                        
                        ticker_el = item.query_selector(Config.SELECTORS['ticker'])
                        
                        raw_title = title_el.inner_text().strip() if title_el else "No Title"
                        raw_ticker_text = ticker_el.inner_text().strip() if ticker_el else ""
                        
                        # usually raw_ticker_text is like "BCDN - 20/01/2026" or just "HPG" depending on site
                        # Let's extract date from there if possible, or from description
                        
                        # Date extraction logic: Look for dd/mm/yyyy
                        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', raw_title + " " + raw_ticker_text)
                        date_str = date_match.group(1) if date_match else datetime.now().strftime('%d/%m/%Y')
                        
                        # Ticker extraction
                        ticker = extract_tickers(raw_title)
                        
                        # Generate ID
                        report_id = hashlib.md5((raw_title + date_str).encode()).hexdigest()
                        
                        if report_id in existing_ids:
                            continue
                            
                        # Need to get PDF Link
                        # Need to get PDF Link
                        # Click icon logic (Most reliable)
                        icon = item.query_selector('.o-simpleReportCard_icon')
                        
                        if icon:
                            # Strategy: Monitor network requests on POPUP
                            pdf_url = ""
                            found_urls = []
                            
                            try:
                                # Trigger click
                                with context.expect_page(timeout=5000) as page_info:
                                    icon.hover()
                                    time.sleep(0.5)
                                    icon.click(force=True)
                                
                                new_page = page_info.value
                                
                                # Listen on popup
                                def handle_popup_request(request):
                                    if '.pdf' in request.url.lower():
                                        found_urls.append(request.url)
                                new_page.on("request", handle_popup_request)
                                
                                try:
                                    # Wait for SPA to load
                                    new_page.wait_for_load_state('networkidle')
                                    
                                    # Check found urls from popup
                                    if not pdf_url and found_urls:
                                        for u in reversed(found_urls):
                                            if '.pdf' in u.lower():
                                                pdf_url = u
                                                break
                                    
                                    # Inspect Popup Content for PDF (fallback)
                                    if not pdf_url:
                                        iframe = new_page.query_selector('iframe')
                                        if iframe:
                                            src = iframe.get_attribute('src')
                                            if src and '.pdf' in src:
                                                pdf_url = src
                                    
                                    # Fallback: viewer URL
                                    if not pdf_url:
                                        pdf_url = new_page.url
                                        
                                    new_page.close()
                                except Exception as e:
                                    print(f"    ⚠️ Error inspecting popup: {e}")
                                    if not new_page.is_closed():
                                        new_page.close()
                                        
                            except Exception as e:
                                print(f"    ⚠️ Popup/Click Error: {e}")
                                pass
                            
                            if not pdf_url and found_urls:
                                pdf_url = found_urls[-1]
                        
                        if pdf_url:
                            new_reports.append({
                                'report_id': report_id,
                                'title': raw_title,
                                'ticker': ticker,
                                'date': date_str,
                                'pdf_url': pdf_url,
                                'download_path': '' 
                            })
                            existing_ids.add(report_id)
                            page_new_count += 1
                            print(f"    ✅ New: {raw_title[:30]}... ({date_str}) | PDF: {pdf_url[:50]}...")
                        
                    except Exception as e:
                        print(f"    ❌ Error processing item: {e}")

                if page_new_count == 0 and current_page > 1:
                    print("🛑 No new reports on this page. Stopping.")
                    break
                
                # Next Page logic
                # VCBS pagination usually has parameters `page=X`
                # We can navigate manually or click next.
                # Let's try navigating manually to handle it cleaner
                current_page += 1
                if current_page <= max_pages:
                    next_url = f"{Config.base_url}?code={type_code}&page={current_page}"
                    print(f"➡️ Going to page {current_page}...")
                    page.goto(next_url, wait_until='networkidle')
                    time.sleep(1) # Chill
            
            browser.close()
            
        self._save_reports(new_reports, csv_path)
        return new_reports

# --- Standard Interface Functions ---

def run(report_type: str = 'bao_cao_doanh_nghiep'):
    """
    Standard run function
    report_type mapping: 
    - 'bao_cao_doanh_nghiep' -> 'BCDN'
    - 'bao_cao_nganh' -> 'BCN'
    """
    code_map = {
        'bao_cao_doanh_nghiep': 'BCDN',
        'bao_cao_nganh': 'BCN'
    }
    
    code = code_map.get(report_type, 'BCDN')
    scanner = VCBSScanner(headless=True)
    scanner.scan_type(code)

def download_by_id(report_id: str, report_type='bao_cao_doanh_nghiep'):
    """Downloads PDF for a specific report ID"""
    print(f"📥 Downloading report {report_id}...")
    
    # Locate report in CSVs
    config = VCBSScanner()
    found_row = None
    target_csv = None
    
    codes = ['BCDN', 'BCN']
    for c in codes:
        _, csv_path = config._get_paths(c)
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
                row = df[df['report_id'] == report_id]
                if not row.empty:
                    found_row = row.iloc[0]
                    target_csv = csv_path
                    target_dir = os.path.dirname(csv_path)
                    break
            except:
                continue
    
    if found_row is None:
        print(f"❌ Report {report_id} not found in any VCBS CSV.")
        return

    pdf_url = found_row['pdf_url']
    if pd.isna(pdf_url) or not pdf_url:
        print("❌ valid PDF URL not found.")
        return

    # Download it
    try:
        # Save dir
        dl_dir = os.path.join(target_dir, "downloads")
        os.makedirs(dl_dir, exist_ok=True)
        
        # Filename
        import slugify # backup
        safe_title = re.sub(r'[^\w\s-]', '', str(found_row['title']))[:50].strip()
        filename = f"{safe_title}_{report_id[:6]}.pdf"
        file_path = os.path.join(dl_dir, filename)
        
        if os.path.exists(file_path):
            print(f"✅ File already exists: {file_path}")
            # Ensure CSV has path
            df = pd.read_csv(target_csv, encoding='utf-8-sig')
            df.loc[df['report_id'] == report_id, 'download_path'] = file_path
            df.to_csv(target_csv, index=False, encoding='utf-8-sig')
            return

        print(f"   Getting: {pdf_url}")
        resp = requests.get(pdf_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        if resp.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(resp.content)
            print(f"✅ Downloaded to: {file_path}")
            
            # Update CSV
            df = pd.read_csv(target_csv, encoding='utf-8-sig')
            df.loc[df['report_id'] == report_id, 'download_path'] = file_path
            df.to_csv(target_csv, index=False, encoding='utf-8-sig')
        else:
            print(f"❌ Failed to download: HTTP {resp.status_code}")
            
    except Exception as e:
        print(f"❌ Download Exception: {e}")

if __name__ == "__main__":
    # Test Run
    print("🧪 Testing VCBS Scanner...")
    # run('bao_cao_doanh_nghiep')
    run('bao_cao_nganh')


