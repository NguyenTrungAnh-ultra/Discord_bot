import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import pickle
import hashlib
import re
from src.utils.base_scanner import BaseScanner
from src.utils.ticker_utils import extract_tickers

class Config:
    bao_cao_cong_ty_url = "https://kbsec.com.vn/vi/bao-cao-cong-ty"
    bao_cao_nganh_url = "https://kbsec.com.vn/vi/bao-cao-nganh"
    base_url = "https://kbsec.com.vn/"

def run(bao_cao_cong_ty_url=False, bao_cao_nganh_url=False):   
    if bao_cao_nganh_url:
        dir_name = os.path.join("KBSV", "bao_cao_nganh")
        bao_cao = Config.bao_cao_nganh_url
    else:
        dir_name = os.path.join("KBSV", "bao_cao_cong_ty")
        bao_cao = Config.bao_cao_cong_ty_url

    scanner = BaseScanner(dir_name, Config.base_url)
    session, old_df, existing_urls = scanner.setup(use_url_as_id=True)
    
    cookie_file = os.path.join(scanner.output_dir, "kbsv_cookies.pkl")
    if os.path.exists(cookie_file):
        try:
            with open(cookie_file, 'rb') as f:
                session.cookies.update(pickle.load(f))
            print("🍪 Đã load cookies từ lần chạy trước")
        except: pass
    
    all_reports = []
    page_num = 1
    max_pages = 10
    found_existing = False
    
    while page_num <= max_pages:
        url = f'{bao_cao}.htm' if page_num == 1 else f"{bao_cao}/p-{page_num}.htm"
        print(f"📄 Đang cào trang {page_num}: {url}")
        
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            items = soup.find_all('div', class_='item')
            
            if not items:
                print(f"⚠️ Không tìm thấy item nào ở trang {page_num}. Dừng lại.")
                break
            
            new_in_page = 0
            for item in items:
                link_tag = item.find('a', href=True)
                if link_tag and link_tag['href'].endswith('.pdf'):
                    pdf_url = link_tag['href']
                    title = link_tag.get('title', 'N/A')
                    
                    date_str = ''
                    date_span = item.find('span', class_='date')
                    if date_span:
                        date_text = date_span.get_text(strip=True)
                        if date_text:
                            date_parts = date_text.split()
                            if date_parts:
                                date_str = date_parts[0]
                    
                    if not pdf_url.startswith('http'):
                        pdf_url = f"https://kbsec.com.vn{pdf_url}"
                    
                    if pdf_url in existing_urls:
                        found_existing = True
                        continue
                    
                    report_id_content = f"{title}|{pdf_url}"
                    report_id = hashlib.md5(report_id_content.encode()).hexdigest()
                    ticker = extract_tickers(title)
                    
                    all_reports.append({
                        'report_id': report_id,
                        'title': title,
                        'ticker': ticker,
                        'date': date_str,
                        'pdf_url': pdf_url,
                        'download_path': ''
                    })
                    new_in_page += 1
            
            print(f"✅ Tìm thấy {new_in_page} báo cáo MỚI từ trang {page_num}")
            if new_in_page == 0 or (found_existing and new_in_page == 0):
                print("🛑 Dừng cào.")
                break
            
            if page_num % 10 == 0:
                time.sleep(random.uniform(2, 5))
            
            page_num += 1
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi khi cào trang {page_num}: {e}")
            break
    
    with open(cookie_file, 'wb') as f:
        pickle.dump(session.cookies, f)
    
    new_df = pd.DataFrame(all_reports)
    if len(new_df) > 0:
        final_df = pd.concat([new_df, old_df], ignore_index=True)
        print(f"\n🎉 Đã thêm {len(new_df)} báo cáo MỚI. Tổng: {len(final_df)} báo cáo.")
    else:
        final_df = old_df
        print(f"\n✨ Không có báo cáo mới. Tổng: {len(final_df)} báo cáo.")
    
    scanner.save_csv(final_df)
    return final_df

def download_by_id(report_id: str, report_type: str = 'bao_cao_cong_ty'):
    dir_name = os.path.join("KBSV", report_type)
    scanner = BaseScanner(dir_name, Config.base_url)
    return scanner.download_by_id(report_id)

def scan_and_download_by_ticker(ticker):
    dir_name = os.path.join("KBSV", "bao_cao_cong_ty")
    scanner = BaseScanner(dir_name, Config.base_url)
    
    ticker = ticker.upper()
    print(f"\n{'='*60}")
    print(f"🔍 Quét báo cáo cho mã: {ticker}")
    print(f"{'='*60}\n")
    
    _, old_df, _ = scanner.setup()
    
    if old_df.empty:
        print("❌ File CSV trống!")
        return {'ticker': ticker, 'total_reports': 0, 'new_reports': 0, 'downloaded': 0, 'reports': []}
    
    ticker_dir = os.path.join(scanner.output_dir, ticker)
    os.makedirs(ticker_dir, exist_ok=True)
    
    ticker_reports = []
    
    for idx, row in old_df.iterrows():
        title = str(row['title'])
        pdf_url = str(row['pdf_url'])
        pdf_filename = pdf_url.split('/')[-1]
        
        is_match = False
        if pdf_filename.startswith('KBSV_'):
            parts = pdf_filename.split('_')
            if len(parts) >= 2 and parts[1].upper() == ticker:
                is_match = True
        
        if not is_match and ticker in title.upper():
            is_match = True
        
        if is_match:
            safe_filename = pdf_filename
            file_path = os.path.join(ticker_dir, safe_filename)
            already_downloaded = os.path.exists(file_path)
            
            ticker_reports.append({
                'title': title,
                'pdf_url': pdf_url,
                'filename': safe_filename,
                'file_path': file_path,
                'downloaded': already_downloaded
            })
    
    new_reports = [r for r in ticker_reports if not r['downloaded']]
    print(f"📊 Kết quả: Tổng số: {len(ticker_reports)} | Chưa tải: {len(new_reports)}")
    
    downloaded_count = 0
    if new_reports:
        print(f"📥 Bắt đầu tải {len(new_reports)} báo cáo mới...\n")
        session, _, _ = scanner.setup()
        for idx, report in enumerate(new_reports, 1):
            print(f"[{idx}/{len(new_reports)}] {report['title']}")
            try:
                response = session.get(report['pdf_url'], timeout=30)
                response.raise_for_status()
                with open(report['file_path'], 'wb') as f:
                    f.write(response.content)
                print(f"   ✅ Đã tải: {report['filename']}")
                downloaded_count += 1
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"   ❌ Lỗi tải: {e}")
                
        cookie_file = os.path.join(scanner.output_dir, "kbsv_cookies.pkl")
        with open(cookie_file, 'wb') as f:
            pickle.dump(session.cookies, f)
            
    return {
        'ticker': ticker,
        'total_reports': len(ticker_reports),
        'new_reports': len(new_reports),
        'downloaded': downloaded_count,
        'reports': ticker_reports
    }

if __name__ == "__main__":
    print("🚀 Starting KBSV Company Reports Scan...\n")
    run(bao_cao_cong_ty_url=True)
    print("\n✅ KBSV scan completed!")
