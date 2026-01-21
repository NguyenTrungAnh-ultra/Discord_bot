import requests
from bs4 import BeautifulSoup
from src.utils.user_agent import get_random_desktop_user_agent
import pandas as pd
import time
import random
import os
import pickle
import hashlib
import json
from datetime import datetime

class Config:
    toan_canh_thi_truong_url = "https://kbsec.com.vn/vi/bao-cao-chien-luoc-thi-truong"
    bao_cao_cong_ty_url = "https://kbsec.com.vn/vi/bao-cao-cong-ty"
    bao_cao_nganh_url = "https://kbsec.com.vn/vi/bao-cao-nganh"
    bao_cao_vimo_url = "https://kbsec.com.vn/vi/bao-cao-trien-vong-kinh-te-vi-mo"
    bao_cao_chuyen_de_url = "https://kbsec.com.vn/vi/bao-cao-chuyen-de"

def file_save(dir):
    # Đường dẫn file
    output_dir = fr".\temp\reports\{dir}"
    csv_file = os.path.join(output_dir, "kbsv_reports.csv")
    cookie_file = os.path.join(output_dir, "kbsv_cookies.pkl")
    
    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(output_dir, exist_ok=True)
    
    # Tạo session để lưu cookies
    session = requests.Session()
    
    # Load cookies nếu có
    if os.path.exists(cookie_file):
        try:
            with open(cookie_file, 'rb') as f:
                session.cookies.update(pickle.load(f))
            print("🍪 Đã load cookies từ lần chạy trước")
        except:
            print("⚠️ Không thể load cookies, sẽ tạo mới")
    
    # Load CSV cũ nếu có
    existing_urls = set()
    old_df = pd.DataFrame()
    if os.path.exists(csv_file):
        try:
            old_df = pd.read_csv(csv_file, encoding='utf-8-sig')
            existing_urls = set(old_df['pdf_url'].tolist())
            print(f"📂 Đã load {len(old_df)} báo cáo cũ từ file CSV")
        except:
            print("⚠️ Không thể load CSV cũ, sẽ tạo mới")
    
    return output_dir, csv_file, cookie_file, session, old_df, existing_urls

def run(toan_canh_thi_truong_url=False, 
                bao_cao_cong_ty_url=False, 
                bao_cao_nganh_url=False,
                bao_cao_vimo_url=False,
                bao_cao_chuyen_de_url=False):   
    
    if toan_canh_thi_truong_url:
        dir = r'KBSV\toan_canh_thi_truong'
        bao_cao = Config.toan_canh_thi_truong_url
    elif bao_cao_cong_ty_url:
        dir = r'KBSV\bao_cao_cong_ty'
        bao_cao = Config.bao_cao_cong_ty_url
    elif bao_cao_nganh_url:
        dir = r'KBSV\bao_cao_nganh'
        bao_cao = Config.bao_cao_nganh_url
    elif bao_cao_vimo_url:
        dir = r'KBSV\bao_cao_vimo'
        bao_cao = Config.bao_cao_vimo_url
    elif bao_cao_chuyen_de_url:
        dir = r'KBSV\bao_cao_chuyen_de'
        bao_cao = Config.bao_cao_chuyen_de_url

    #load/ceate file 
    output_dir, csv_file, cookie_file, session, old_df, existing_urls = file_save(dir)
    
    # Tạo headers từ user agent ngẫu nhiên
    user_agent = get_random_desktop_user_agent()
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
        "Referer": "https://kbsec.com.vn/"
    }
    
    all_reports = []
    page_num = 1
    max_pages = 10  # Tăng lên để cào đủ nếu lần đầu
    found_existing = False  # Flag để dừng khi gặp báo cáo cũ
    
    while page_num <= max_pages:
        if page_num == 1:
            url = f'{bao_cao}'+".htm"
        else:
            url = f"{bao_cao}/p-{page_num}.htm"
        
        print(f"📄 Đang cào trang {page_num}: {url}")
        
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm tất cả div.item
            items = soup.find_all('div', class_='item')
            
            if not items:
                print(f"⚠️ Không tìm thấy item nào ở trang {page_num}. Dừng lại.")
                break
            
            new_in_page = 0
            for item in items:
                # Tìm thẻ <a> chứa link PDF
                link_tag = item.find('a', href=True)
                if link_tag and link_tag['href'].endswith('.pdf'):
                    pdf_url = link_tag['href']
                    title = link_tag.get('title', 'N/A')
                    
                    # Extract date from span.date
                    date_str = ''
                    date_span = item.find('span', class_='date')
                    if date_span:
                        # Date format: "07/01/2026 02:39:51 PM"
                        # We only need the date part: "07/01/2026"
                        date_text = date_span.get_text(strip=True)
                        if date_text:
                            # Extract DD/MM/YYYY part
                            date_parts = date_text.split()
                            if date_parts:
                                date_str = date_parts[0]  # "07/01/2026"
                    
                    # Nếu link là relative, thêm domain
                    if not pdf_url.startswith('http'):
                        pdf_url = f"https://kbsec.com.vn{pdf_url}"
                    
                    # Kiểm tra xem đã có trong DB cũ chưa
                    if pdf_url in existing_urls:
                        found_existing = True
                        continue  # Bỏ qua báo cáo đã có
                    
                    # Generate report_id (giống VCBS/ACBS/SSI)
                    report_id_content = f"{title}|{pdf_url}"
                    report_id = hashlib.md5(report_id_content.encode()).hexdigest()
                    
                    # Extract ticker from title if possible
                    ticker = ''
                    title_parts = title.split('-')
                    if len(title_parts) > 0:
                        potential_ticker = title_parts[0].strip().upper()
                        if len(potential_ticker) >= 3 and len(potential_ticker) <= 4:
                            ticker = potential_ticker
                    
                    all_reports.append({
                        'report_id': report_id,
                        'title': title,
                        'ticker': ticker,
                        'date': date_str,
                        'pdf_url': pdf_url,
                        'download_url': pdf_url,
                        'downloaded': False,
                        'download_path': ''
                    })
                    new_in_page += 1
            
            print(f"✅ Tìm thấy {new_in_page} báo cáo MỚI từ trang {page_num}")
            if new_in_page == 0:
                print('new_in_page = 0')
                break

            # Nếu đã gặp báo cáo cũ và không có báo cáo mới nào ở trang này, dừng lại
            if found_existing and new_in_page == 0:
                print("🛑 Đã gặp toàn báo cáo cũ, dừng cào.")
                break
            
            # Nghỉ sau mỗi 10 trang
            if page_num % 10 == 0:
                sleep_time = random.uniform(2, 5)
                print(f"😴 Nghỉ {sleep_time:.1f}s sau 10 trang...")
                time.sleep(sleep_time)
            
            page_num += 1
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi khi cào trang {page_num}: {e}")
            break
    
    # Lưu cookies
    with open(cookie_file, 'wb') as f:
        pickle.dump(session.cookies, f)
    print(f"🍪 Đã lưu cookies vào: {cookie_file}")
    
    # Tạo DataFrame mới
    new_df = pd.DataFrame(all_reports)
    
    if len(new_df) > 0:
        # Thêm báo cáo mới vào ĐẦU file cũ (giữ thứ tự mới nhất trước)
        final_df = pd.concat([new_df, old_df], ignore_index=True)
        print(f"\n🎉 Đã thêm {len(new_df)} báo cáo MỚI. Tổng: {len(final_df)} báo cáo.")
    else:
        final_df = old_df
        print(f"\n✨ Không có báo cáo mới. Tổng: {len(final_df)} báo cáo.")
    
    print(final_df.head(10))
    
    # Lưu ra file CSV
    final_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"💾 Đã lưu vào file: {csv_file}")
    
    return final_df

def scan_and_download_by_ticker(ticker):
    """
    Quét và tải báo cáo theo mã cổ phiếu từ CSV có sẵn
    
    Args:
        ticker: Mã cổ phiếu (ví dụ: 'VNM', 'HPG', 'STB')
    
    Returns:
        dict: {
            'ticker': mã cổ phiếu,
            'total_reports': tổng số báo cáo tìm thấy,
            'new_reports': số báo cáo chưa tải,
            'downloaded': số báo cáo đã tải thành công,
            'reports': list các báo cáo
        }
    """
    ticker = ticker.upper()
    print(f"\n{'='*60}")
    print(f"🔍 Quét báo cáo cho mã: {ticker}")
    print(f"{'='*60}\n")
    
    # Load/create file
    dir = r'KBSV\bao_cao_cong_ty'
    output_dir, csv_file, cookie_file, session, old_df, existing_urls = file_save(dir)
    
    # Kiểm tra CSV có dữ liệu không
    if old_df.empty:
        print("❌ File CSV trống! Vui lòng chạy hàm run() trước để cào dữ liệu.")
        return {
            'ticker': ticker,
            'total_reports': 0,
            'new_reports': 0,
            'downloaded': 0,
            'reports': []
        }
    
    # Tạo thư mục con cho ticker
    ticker_dir = os.path.join(output_dir, ticker)
    os.makedirs(ticker_dir, exist_ok=True)
    
    # Lọc báo cáo theo ticker
    # Cách 1: Tìm trong title
    # Cách 2: Tìm trong tên file PDF (format: KBSV_{TICKER}_*.pdf)
    ticker_reports = []
    
    for idx, row in old_df.iterrows():
        title = str(row['title'])
        pdf_url = str(row['pdf_url'])
        
        # Extract tên file từ URL
        pdf_filename = pdf_url.split('/')[-1]  # Ví dụ: KBSV_STB_FTM.pdf
        
        # Kiểm tra ticker trong tên file hoặc title
        # Format KBSV: KBSV_{TICKER}_*.pdf
        is_match = False
        
        # Check trong tên file (ưu tiên)
        if pdf_filename.startswith('KBSV_'):
            parts = pdf_filename.split('_')
            if len(parts) >= 2 and parts[1].upper() == ticker:
                is_match = True
        
        # Check trong title (backup)
        if not is_match and ticker in title.upper():
            is_match = True
        
        if is_match:
            # Tạo tên file an toàn từ title
            safe_filename = title.replace('/', '-').replace('\\', '-').replace(':', '-')
            # Hoặc dùng luôn tên file gốc
            safe_filename = pdf_filename
            
            # Check xem file đã tải chưa
            file_path = os.path.join(ticker_dir, safe_filename)
            already_downloaded = os.path.exists(file_path)
            
            ticker_reports.append({
                'title': title,
                'pdf_url': pdf_url,
                'filename': safe_filename,
                'file_path': file_path,
                'downloaded': already_downloaded
            })
    
    # Thống kê
    total_reports = len(ticker_reports)
    new_reports = [r for r in ticker_reports if not r['downloaded']]
    
    print(f"📊 Kết quả tìm kiếm:")
    print(f"   • Tổng số báo cáo: {total_reports}")
    print(f"   • Báo cáo chưa tải: {len(new_reports)}")
    print(f"   • Báo cáo đã có: {total_reports - len(new_reports)}")
    print(f"{'='*60}\n")
    
    # Hiển thị danh sách báo cáo tìm thấy
    if ticker_reports:
        print("📋 Danh sách báo cáo:")
        for i, report in enumerate(ticker_reports, 1):
            status = "✅" if report['downloaded'] else "⬇️"
            print(f"   {i}. {status} {report['title']}")
        print()
    
    # Tải các báo cáo mới
    downloaded_count = 0
    if new_reports:
        # Tạo headers
        user_agent = get_random_desktop_user_agent()
        headers = {
            "User-Agent": user_agent,
            "Accept": "application/pdf,*/*",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
            "Referer": "https://kbsec.com.vn/"
        }
        
        print(f"📥 Bắt đầu tải {len(new_reports)} báo cáo mới...\n")
        
        for idx, report in enumerate(new_reports, 1):
            print(f"[{idx}/{len(new_reports)}] {report['title']}")
            
            try:
                # Tải PDF với session (có cookie)
                response = session.get(report['pdf_url'], headers=headers, timeout=30)
                response.raise_for_status()
                
                # Lưu file
                with open(report['file_path'], 'wb') as f:
                    f.write(response.content)
                
                file_size = len(response.content) / 1024  # KB
                print(f"   ✅ Đã tải: {report['filename']} ({file_size:.1f} KB)")
                downloaded_count += 1
                
                # Delay giữa các lần tải
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"   ❌ Lỗi tải: {e}")
    else:
        print("✨ Không có báo cáo mới cần tải.\n")
    
    # Lưu cookies
    with open(cookie_file, 'wb') as f:
        pickle.dump(session.cookies, f)
    print(f"🍪 Đã lưu cookies\n")
    
    return {
        'ticker': ticker,
        'total_reports': total_reports,
        'new_reports': len(new_reports),
        'downloaded': downloaded_count,
        'reports': ticker_reports
    }


if __name__ == "__main__":
    # Scan all company reports
    print("🚀 Starting KBSV Company Reports Scan...\n")
    run(bao_cao_cong_ty_url=True)
    print("\n✅ KBSV scan completed!")


