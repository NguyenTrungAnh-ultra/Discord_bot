"""
ACBS Report Scraper
Scrapes financial reports from ACBS website (bao_cao_doanh_nghiep only)
Structure aligned with KBSV report scraper
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import hashlib
import os
from datetime import datetime
import time
import random
import re
from src.utils.user_agent import get_random_desktop_user_agent


class Config:
    """Configuration for ACBS scraper"""
    base_url = "https://acbs.com.vn"
    bao_cao_doanh_nghiep_url = "https://acbs.com.vn/trung-tam-phan-tich/bao-cao-doanh-nghiep"
    
    max_pages = 10
    request_timeout = 30


def file_save():
    """Setup directories and load existing data (like KBSV)"""
    output_dir = r".\temp\reports\ACBS"
    csv_file = os.path.join(output_dir, "acbs_reports.csv")
    
    # Create directory if not exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create session
    session = requests.Session()
    user_agent = get_random_desktop_user_agent()
    session.headers.update({
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        'Referer': 'https://acbs.com.vn/'
    })
    
    # Load existing CSV
    existing_ids = set()
    old_df = pd.DataFrame()
    if os.path.exists(csv_file):
        try:
            old_df = pd.read_csv(csv_file, encoding='utf-8-sig')
            if 'report_id' in old_df.columns:
                existing_ids = set(old_df['report_id'].tolist())
            print(f"📂 Đã load {len(old_df)} báo cáo cũ từ file CSV")
        except:
            print("⚠️ Không thể load CSV cũ, sẽ tạo mới")
    
    return output_dir, csv_file, session, old_df, existing_ids


def _extract_pdf_url(session, detail_url):
    """Visit detail page and extract PDF URL"""
    try:
        response = session.get(detail_url, timeout=Config.request_timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find PDF link - look for "Tải xuống" or "Xem trước" links
        # These typically have class containing "flex gap-4 items-center"
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
        
        for link in pdf_links:
            href = link.get('href', '')
            if href.endswith('.pdf'):
                # Make full URL if relative
                if href.startswith('/'):
                    return Config.base_url + href
                elif href.startswith('http'):
                    return href
                else:
                    return Config.base_url + '/' + href
        
        # Fallback: look for any PDF link in the page
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if '.pdf' in href.lower():
                if href.startswith('/'):
                    return Config.base_url + href
                elif href.startswith('http'):
                    return href
                    
        return ''
        
    except Exception as e:
        print(f"⚠️ Lỗi khi lấy PDF URL từ {detail_url}: {e}")
        return ''


def _extract_date_from_element(element):
    """Extract date from report card element"""
    # Look for date in various formats
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
    ]
    
    # Try to find date in text content
    text = element.get_text()
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups[0]) == 4:  # YYYY/MM/DD format
                return f"{groups[2]}/{groups[1]}/{groups[0]}"
            else:  # DD/MM/YYYY format
                return f"{groups[0]}/{groups[1]}/{groups[2]}"
    
    return ''


def extract_tickers(title: str) -> str:
    """
    Trích xuất mã cổ phiếu từ title
    - Trả về các mã cách nhau bằng dấu phẩy
    - Trả về None nếu không tìm thấy
    """
    # Các từ không phải mã cổ phiếu
    excluded = {
        'CTCP', 'TCT', 'TNHH', 'ABB', 'CEO', 'CFO', 'COO', 'MUA', 'BAN', 'GIỮ',
        'VND', 'USD', 'EUR', 'JPY', 'VNĐ', 'PDF', 'Q1', 'Q2', 'Q3', 'Q4',
        'FY', 'YTD', 'TTM', 'EPS', 'P/E', 'ROE', 'ROA', 'CAGR', 'EBITDA',
        'KHẢ', 'QUAN', 'CẬP', 'NHẬT', 'BAO', 'CAO', 'NHANH', 'KHÔNG', 'ĐÁNH',
        'GIÁ', 'CTCP', 'CÔNG', 'TY', 'CỔ', 'PHẦN', 'NGÂN', 'HÀNG', 'TMCP',
        'LNST', 'SVCK', 'THU', 'GIAO', 'CHUY', 'HSX', 'HNX', 'UPCOM', 'VNIND',
        'VNI', 'VN30', 'TRU', 'TANG', 'GIAM', 'LOI', 'NHUAN', 'DOANH', 'THUE',
        'QUY', 'NAM', 'THANG', 'TUAN', 'NGAY'
    }
    
    # Tìm tất cả mã 3-4 ký tự viết hoa (xử lý cả trường hợp _VCG_)
    tickers = re.findall(r'(?<![A-Za-z0-9])([A-Z]{3,4})(?![A-Za-z0-9])', title.upper())
    
    # Loại bỏ các từ không phải mã
    tickers = [t for t in tickers if t not in excluded]
    
    # Loại bỏ trùng lặp và sắp xếp
    unique_tickers = sorted(set(tickers))
    
    if unique_tickers:
        return ','.join(unique_tickers)
    return None


def run():
    """
    Main scrape function - scrapes báo cáo doanh nghiệp
    Returns DataFrame of reports
    """
    print("\n" + "="*60)
    print("🔍 ACBS - Báo cáo Doanh nghiệp Scraper")
    print("="*60 + "\n")
    
    # Setup
    output_dir, csv_file, session, old_df, existing_ids = file_save()
    
    all_reports = []
    page_num = 1
    found_existing = False
    
    while page_num <= Config.max_pages:
        # Construct URL with pagination
        if page_num == 1:
            url = Config.bao_cao_doanh_nghiep_url
        else:
            url = f"{Config.bao_cao_doanh_nghiep_url}?paged={page_num}"
        
        print(f"📄 Đang cào trang {page_num}: {url}")
        
        try:
            response = session.get(url, timeout=Config.request_timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find report cards with class "group space-y-6 flex flex-col"
            report_cards = soup.find_all('div', class_=re.compile(r'group.*space-y-6.*flex.*flex-col'))
            
            # Fallback: find any links to chi-tiet pages
            if not report_cards:
                report_cards = soup.find_all('a', href=re.compile(r'/trung-tam-phan-tich/chi-tiet/'))
            
            if not report_cards:
                print(f"⚠️ Không tìm thấy báo cáo ở trang {page_num}. Dừng lại.")
                break
            
            print(f"📋 Tìm thấy {len(report_cards)} items")
            
            new_in_page = 0
            
            for card in report_cards:
                try:
                    # Find "Xem ngay" link
                    xem_ngay_link = card.find('a', string=re.compile(r'Xem ngay', re.I))
                    if not xem_ngay_link:
                        # Try to find any link with chi-tiet
                        xem_ngay_link = card.find('a', href=re.compile(r'/trung-tam-phan-tich/chi-tiet/'))
                    
                    if not xem_ngay_link:
                        # If card is itself a link
                        if card.name == 'a' and '/trung-tam-phan-tich/chi-tiet/' in card.get('href', ''):
                            xem_ngay_link = card
                        else:
                            continue
                    
                    detail_url = xem_ngay_link.get('href', '')
                    if not detail_url:
                        continue
                    
                    # Make full URL
                    if detail_url.startswith('/'):
                        detail_url = Config.base_url + detail_url
                    
                    # Find title - look for heading or strong text
                    title_elem = card.find(['h1', 'h2', 'h3', 'h4', 'strong'])
                    if not title_elem:
                        # Get title from link text
                        all_text = card.get_text(strip=True)
                        # Remove "Xem ngay" and clean up
                        title = all_text.replace('Xem ngay', '').strip()
                        title = re.sub(r'Báo cáo Ngành & Doanh nghiệp', '', title).strip()
                    else:
                        title = title_elem.get_text(strip=True)
                    
                    # Clean up title - remove timestamp prefix like "5:18:28 Chiều-10/12/2025"
                    # Pattern: HH:MM:SS (Sáng|Chiều)-DD/MM/YYYY
                    title = re.sub(r'^\d{1,2}:\d{2}:\d{2}\s*(Sáng|Chiều)-\d{1,2}/\d{1,2}/\d{4}', '', title).strip()
                    
                    # Also clean up date patterns at start like "10/12/2025"
                    title = re.sub(r'^\d{1,2}/\d{1,2}/\d{4}\s*', '', title).strip()
                    
                    # Truncate title - often the description is concatenated after the title
                    # The title usually ends before the description (company full name or details)
                    # Common patterns: "Cập nhật XXX – Khuyến nghịDescription..."
                    # We'll take a reasonable length for the title
                    if len(title) > 100:
                        # Try to find a natural break point
                        break_patterns = [
                            r'(Chúng tôi)',  # Start of description
                            r'(CTCP\s+[A-Z])',  # Company full name
                            r'(NGÂN\s+HÀNG)',  # Bank full name
                            r'(TCT\s+[A-Z])',  # Corporation name
                            r'(Q[1-4]\.20\d{2},)',  # Quarterly result intro
                            r'(TỔNG\s+CÔNG)',  # General corporation
                        ]
                        for pattern in break_patterns:
                            match = re.search(pattern, title, re.IGNORECASE)
                            if match and match.start() > 20:
                                title = title[:match.start()].strip()
                                break
                        else:
                            # If no pattern found, truncate at 100 chars
                            title = title[:100].strip()
                    
                    if not title or title in ['Xem ngay', '']:
                        continue
                    
                    # Extract date
                    date_str = _extract_date_from_element(card)
                    
                    # Generate report ID (before getting PDF to avoid unnecessary requests)
                    report_id_content = f"{title}|{detail_url}"
                    report_id = hashlib.md5(report_id_content.encode()).hexdigest()
                    
                    # Check if already exists
                    if report_id in existing_ids:
                        found_existing = True
                        continue
                    
                    # Extract ticker(s) from title
                    ticker = extract_tickers(title)
                    
                    # Get PDF URL from detail page
                    print(f"  📎 Lấy PDF URL: {title[:50]}...")
                    pdf_url = _extract_pdf_url(session, detail_url)
                    
                    if not pdf_url:
                        print(f"  ⚠️ Không tìm thấy PDF cho: {title[:50]}")
                        continue
                    
                    # Create report record (matching KBSV structure)
                    all_reports.append({
                        'report_id': report_id,
                        'title': title,
                        'ticker': ticker,
                        'date': date_str,
                        'pdf_url': pdf_url,
                        'download_path': ''
                    })
                    
                    new_in_page += 1
                    
                    # Small delay to be respectful
                    time.sleep(random.uniform(0.3, 0.8))
                    
                except Exception as e:
                    print(f"  ⚠️ Lỗi xử lý item: {e}")
                    continue
            
            print(f"✅ Tìm thấy {new_in_page} báo cáo MỚI từ trang {page_num}")
            
            if new_in_page == 0:
                print("🛑 Không có báo cáo mới, dừng cào.")
                break
            
            # If found existing and no new, stop
            if found_existing and new_in_page == 0:
                print("🛑 Đã gặp toàn báo cáo cũ, dừng cào.")
                break
            
            page_num += 1
            
            # Rest after every 5 pages
            if page_num % 5 == 0:
                sleep_time = random.uniform(2, 4)
                print(f"😴 Nghỉ {sleep_time:.1f}s sau 5 trang...")
                time.sleep(sleep_time)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi khi cào trang {page_num}: {e}")
            break
    
    # Create new DataFrame
    new_df = pd.DataFrame(all_reports)
    
    if len(new_df) > 0:
        # Prepend new reports to old (newest first)
        final_df = pd.concat([new_df, old_df], ignore_index=True)
        print(f"\n🎉 Đã thêm {len(new_df)} báo cáo MỚI. Tổng: {len(final_df)} báo cáo.")
    else:
        final_df = old_df
        print(f"\n✨ Không có báo cáo mới. Tổng: {len(final_df)} báo cáo.")
    
    # Ensure columns are in correct order
    expected_columns = ['report_id', 'title', 'ticker', 'date', 'pdf_url', 'download_path']
    for col in expected_columns:
        if col not in final_df.columns:
            final_df[col] = ''
    final_df = final_df[expected_columns]
    
    # Save CSV
    final_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"💾 Đã lưu vào file: {csv_file}")
    
    print(final_df.head(10))
    
    return final_df


def download_by_id(report_id):
    """
    Download PDF by report ID
    
    Args:
        report_id: MD5 hash ID of the report
        
    Returns:
        dict: {
            'success': bool,
            'report_id': str,
            'title': str,
            'file_path': str,
            'error': str (if failed)
        }
    """
    output_dir = r".\temp\reports\ACBS"
    csv_file = os.path.join(output_dir, "acbs_reports.csv")
    
    # Load CSV
    if not os.path.exists(csv_file):
        return {
            'success': False,
            'report_id': report_id,
            'title': '',
            'file_path': '',
            'error': 'CSV file not found. Run run() first.'
        }
    
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
    except Exception as e:
        return {
            'success': False,
            'report_id': report_id,
            'title': '',
            'file_path': '',
            'error': f'Error loading CSV: {e}'
        }
    
    # Find report
    report = df[df['report_id'] == report_id]
    if report.empty:
        return {
            'success': False,
            'report_id': report_id,
            'title': '',
            'file_path': '',
            'error': f'Report not found with ID: {report_id}'
        }
    
    report_row = report.iloc[0]
    pdf_url = report_row.get('pdf_url', '')
    title = report_row.get('title', '')
    
    if not pdf_url or pd.isna(pdf_url):
        return {
            'success': False,
            'report_id': report_id,
            'title': title,
            'file_path': '',
            'error': 'No PDF URL for this report'
        }
    
    # Check if already downloaded
    existing_path = report_row.get('download_path', '')
    if existing_path and not pd.isna(existing_path) and os.path.exists(existing_path):
        print(f"✅ File đã tồn tại: {existing_path}")
        return {
            'success': True,
            'report_id': report_id,
            'title': title,
            'file_path': existing_path,
            'error': ''
        }
    
    # Create download directory
    download_dir = os.path.join(output_dir, "downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    # Generate filename from URL
    filename = pdf_url.split('/')[-1]
    if not filename.endswith('.pdf'):
        filename = f"{report_id[:8]}.pdf"
    
    file_path = os.path.join(download_dir, filename)
    
    # Download PDF
    print(f"📥 Đang tải: {title[:50]}...")
    
    try:
        session = requests.Session()
        user_agent = get_random_desktop_user_agent()
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/pdf,*/*',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Referer': 'https://acbs.com.vn/'
        })
        
        response = session.get(pdf_url, timeout=60)
        response.raise_for_status()
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        file_size = len(response.content) / 1024
        print(f"✅ Đã tải: {filename} ({file_size:.1f} KB)")
        
        # Update CSV
        df.loc[df['report_id'] == report_id, 'download_path'] = file_path
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        return {
            'success': True,
            'report_id': report_id,
            'title': title,
            'file_path': file_path,
            'error': ''
        }
        
    except Exception as e:
        print(f"❌ Lỗi tải file: {e}")
        return {
            'success': False,
            'report_id': report_id,
            'title': title,
            'file_path': '',
            'error': str(e)
        }


if __name__ == "__main__":
    print("🚀 Starting ACBS Report Scraper...\n")
    df = run()
    print("\n✅ ACBS scan completed!")
