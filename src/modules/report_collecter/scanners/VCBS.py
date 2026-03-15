"""
VCBS Report Scraper (Playwright Version)
Scrapes financial reports from VCBS website using Playwright.
Handles dynamic buttons (click to get link).

report_id: MD5 hash of title only — STABLE, không phụ thuộc vào ngày tháng.
"""

import os
import re
import time
import hashlib
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from playwright.sync_api import sync_playwright


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
        'next_page': 'button.pagination-next',
        'disabled_next': 'button.pagination-next[disabled]'
    }

    # Timeouts
    page_load_timeout = 60000
    element_timeout = 5000

    # Limits
    max_pages = 5  # Scan latest 5 pages by default to be safe

    # CSV columns — chỉ 4 cột, không có ticker/download_path
    CSV_COLUMNS = ['report_id', 'title', 'date', 'pdf_url']


def generate_report_id(title: str) -> str:
    """
    Tạo report_id DUY NHẤT và ỔN ĐỊNH từ title.
    KHÔNG phụ thuộc vào ngày tháng hay bất kỳ thứ gì khác.
    """
    return hashlib.md5(title.strip().encode('utf-8')).hexdigest()


class VCBSScanner:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_dir = os.path.join(os.getcwd(), "temp", "reports", "VCBS")

    def _get_paths(self, report_type_code: str) -> Tuple[str, str]:
        """Get output directory and CSV path"""
        dir_name = "bao_cao_doanh_nghiep" if report_type_code == "BCDN" else "bao_cao_nganh"
        out_dir = os.path.join(self.base_dir, dir_name)
        os.makedirs(out_dir, exist_ok=True)
        return out_dir, os.path.join(out_dir, "vcbs_reports.csv")

    def _load_existing_ids(self, csv_path: str) -> set:
        """Load existing report_ids (dựa trên title hash)"""
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path, encoding='utf-8-sig')
                if 'report_id' in df.columns:
                    return set(df['report_id'].astype(str).tolist())
            except Exception:
                pass
        return set()

    def _save_reports(self, reports: List[Dict], csv_path: str):
        """Merge new reports vào CSV, dedup theo report_id (= title hash)"""
        if not reports:
            print("ℹ️ Không có báo cáo mới.")
            return

        new_df = pd.DataFrame(reports)[Config.CSV_COLUMNS]

        if os.path.exists(csv_path):
            try:
                old_df = pd.read_csv(csv_path, encoding='utf-8-sig')
                # Chỉ giữ các cột chuẩn
                for col in Config.CSV_COLUMNS:
                    if col not in old_df.columns:
                        old_df[col] = ''
                old_df = old_df[Config.CSV_COLUMNS]

                combined = pd.concat([new_df, old_df], ignore_index=True)
                # Dedup theo report_id (title hash); giữ bản đầu tiên = mới nhất
                combined.drop_duplicates(subset='report_id', keep='first', inplace=True)
                combined.to_csv(csv_path, index=False, encoding='utf-8-sig')
                print(f"💾 Saved {len(reports)} new, total {len(combined)} reports → {csv_path}")
            except Exception as e:
                print(f"⚠️ Merge error: {e}, overwriting")
                new_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        else:
            new_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"💾 Created CSV with {len(reports)} reports → {csv_path}")

    def scan_type(self, type_code: str, max_pages: int = Config.max_pages):
        print(f"\n🚀 Scanning VCBS: {Config.report_type_names.get(type_code, type_code)}")
        out_dir, csv_path = self._get_paths(type_code)
        existing_ids = self._load_existing_ids(csv_path)

        new_reports = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                           '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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

                try:
                    page.wait_for_selector(Config.SELECTORS['list_item'], timeout=10000)
                except Exception:
                    print("⚠️ No reports found (selector timeout).")
                    break

                items = page.query_selector_all(Config.SELECTORS['list_item'])
                print(f"   Found {len(items)} items.")

                page_new_count = 0

                for item in items:
                    try:
                        title_el = item.query_selector(Config.SELECTORS['title'])
                        ticker_el = item.query_selector(Config.SELECTORS['ticker'])

                        raw_title = title_el.inner_text().strip() if title_el else "No Title"
                        raw_ticker_text = ticker_el.inner_text().strip() if ticker_el else ""

                        # Date extraction: dd/mm/yyyy or dd.mm.yyyy or dd-mm-yyyy
                        date_match = re.search(
                            r'(\d{2}[/.\-]\d{2}[/.\-]\d{4})',
                            raw_title + " " + raw_ticker_text
                        )
                        if date_match:
                            date_str = date_match.group(1).replace('.', '/').replace('-', '/')
                        else:
                            date_str = datetime.now().strftime('%d/%m/%Y')

                        # report_id CHỈ dựa trên title
                        report_id = generate_report_id(raw_title)

                        if report_id in existing_ids:
                            continue

                        # Get PDF link by clicking icon
                        pdf_url = ""
                        icon = item.query_selector('.o-simpleReportCard_icon')

                        if icon:
                            found_urls = []
                            try:
                                with context.expect_page(timeout=5000) as page_info:
                                    icon.hover()
                                    time.sleep(0.5)
                                    icon.click(force=True)

                                new_page = page_info.value

                                def handle_popup_request(request):
                                    if '.pdf' in request.url.lower():
                                        found_urls.append(request.url)

                                new_page.on("request", handle_popup_request)

                                try:
                                    new_page.wait_for_load_state('networkidle')

                                    if not pdf_url and found_urls:
                                        for u in reversed(found_urls):
                                            if '.pdf' in u.lower():
                                                pdf_url = u
                                                break

                                    if not pdf_url:
                                        iframe = new_page.query_selector('iframe')
                                        if iframe:
                                            src = iframe.get_attribute('src')
                                            if src and '.pdf' in src:
                                                pdf_url = src

                                    if not pdf_url:
                                        pdf_url = new_page.url

                                    new_page.close()
                                except Exception as e:
                                    print(f"    ⚠️ Error inspecting popup: {e}")
                                    if not new_page.is_closed():
                                        new_page.close()

                            except Exception as e:
                                print(f"    ⚠️ Popup/Click Error: {e}")

                            if not pdf_url and found_urls:
                                pdf_url = found_urls[-1]

                        if pdf_url:
                            new_reports.append({
                                'report_id': report_id,
                                'title': raw_title,
                                'date': date_str,
                                'pdf_url': pdf_url,
                            })
                            existing_ids.add(report_id)
                            page_new_count += 1
                            print(f"    ✅ New: {raw_title[:40]}... ({date_str})")

                    except Exception as e:
                        print(f"    ❌ Error processing item: {e}")

                if page_new_count == 0 and current_page > 1:
                    print("🛑 No new reports on this page. Stopping.")
                    break

                current_page += 1
                if current_page <= max_pages:
                    next_url = f"{Config.base_url}?code={type_code}&page={current_page}"
                    print(f"➡️ Going to page {current_page}...")
                    page.goto(next_url, wait_until='networkidle')
                    time.sleep(1)

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
    """Downloads PDF for a specific report_id"""
    import requests
    print(f"📥 Downloading report {report_id}...")

    config = VCBSScanner()
    found_row = None
    target_csv = None
    target_dir = None

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
            except Exception:
                continue

    if found_row is None:
        print(f"❌ Report {report_id} not found in any VCBS CSV.")
        return

    pdf_url = found_row['pdf_url']
    if pd.isna(pdf_url) or not pdf_url:
        print("❌ Valid PDF URL not found.")
        return

    try:
        dl_dir = os.path.join(target_dir, "downloads")
        os.makedirs(dl_dir, exist_ok=True)

        safe_title = re.sub(r'[^\w\s\-]', '', str(found_row['title']))[:50].strip()
        filename = f"{safe_title}_{report_id[:6]}.pdf"
        file_path = os.path.join(dl_dir, filename)

        if os.path.exists(file_path):
            print(f"✅ File already exists: {file_path}")
            return

        print(f"   Getting: {pdf_url}")
        resp = requests.get(pdf_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        if resp.status_code == 200:
            with open(file_path, 'wb') as f:
                f.write(resp.content)
            print(f"✅ Downloaded to: {file_path}")
        else:
            print(f"❌ Failed to download: HTTP {resp.status_code}")

    except Exception as e:
        print(f"❌ Download Exception: {e}")


if __name__ == "__main__":
    print("🧪 Testing VCBS Scanner...")
    # run('bao_cao_doanh_nghiep')
    run('bao_cao_nganh')
