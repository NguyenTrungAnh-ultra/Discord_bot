"""
ACBS Report Scraper
Scrapes financial reports from ACBS website (bao_cao_doanh_nghiep only)
Refactored to use BaseScanner
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import hashlib
import time
import random
import re
from src.core.scraper.base import BaseScanner
from src.utils.ticker import extract_tickers

class Config:
    """Configuration for ACBS scraper"""
    base_url = "https://acbs.com.vn"
    bao_cao_doanh_nghiep_url = "https://acbs.com.vn/trung-tam-phan-tich/bao-cao-doanh-nghiep"
    max_pages = 10
    request_timeout = 30

def _extract_pdf_url(session, detail_url):
    """Visit detail page and extract PDF URL"""
    try:
        response = session.get(detail_url, timeout=Config.request_timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
        
        for link in pdf_links:
            href = link.get('href', '')
            if href.endswith('.pdf'):
                if href.startswith('/'): return Config.base_url + href
                elif href.startswith('http'): return href
                else: return Config.base_url + '/' + href
        
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if '.pdf' in href.lower():
                if href.startswith('/'): return Config.base_url + href
                elif href.startswith('http'): return href
                    
        return ''
    except Exception as e:
        print(f"⚠️ Lỗi khi lấy PDF URL từ {detail_url}: {e}")
        return ''

def _extract_date_from_element(element):
    """Extract date from report card element"""
    date_patterns = [
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
    ]
    text = element.get_text()
    
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups[0]) == 4:
                return f"{groups[2]}/{groups[1]}/{groups[0]}"
            else:
                return f"{groups[0]}/{groups[1]}/{groups[2]}"
    
    return ''

def run():
    print("\n" + "="*60)
    print("🔍 ACBS - Báo cáo Doanh nghiệp Scraper")
    print("="*60 + "\n")
    
    scanner = BaseScanner("ACBS", Config.base_url)
    session, old_df, existing_ids = scanner.setup()
    
    all_reports = []
    page_num = 1
    found_existing = False
    
    while page_num <= Config.max_pages:
        url = Config.bao_cao_doanh_nghiep_url if page_num == 1 else f"{Config.bao_cao_doanh_nghiep_url}?paged={page_num}"
        print(f"📄 Đang cào trang {page_num}: {url}")
        
        try:
            response = session.get(url, timeout=Config.request_timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            report_cards = soup.find_all('div', class_=re.compile(r'group.*space-y-6.*flex.*flex-col'))
            if not report_cards:
                report_cards = soup.find_all('a', href=re.compile(r'/trung-tam-phan-tich/chi-tiet/'))
            
            if not report_cards:
                print(f"⚠️ Không tìm thấy báo cáo ở trang {page_num}. Dừng lại.")
                break
            
            print(f"📋 Tìm thấy {len(report_cards)} items")
            new_in_page = 0
            
            for card in report_cards:
                try:
                    xem_ngay_link = card.find('a', string=re.compile(r'Xem ngay', re.I))
                    if not xem_ngay_link:
                        xem_ngay_link = card.find('a', href=re.compile(r'/trung-tam-phan-tich/chi-tiet/'))
                    
                    if not xem_ngay_link:
                        if card.name == 'a' and '/trung-tam-phan-tich/chi-tiet/' in card.get('href', ''):
                            xem_ngay_link = card
                        else:
                            continue
                    
                    detail_url = xem_ngay_link.get('href', '')
                    if not detail_url: continue
                    if detail_url.startswith('/'): detail_url = Config.base_url + detail_url
                    
                    title_elem = card.find(['h1', 'h2', 'h3', 'h4', 'strong'])
                    if not title_elem:
                        title = card.get_text(strip=True).replace('Xem ngay', '').strip()
                        title = re.sub(r'Báo cáo Ngành & Doanh nghiệp', '', title).strip()
                    else:
                        title = title_elem.get_text(strip=True)
                    
                    title = re.sub(r'^\d{1,2}:\d{2}:\d{2}\s*(Sáng|Chiều)-\d{1,2}/\d{1,2}/\d{4}', '', title).strip()
                    title = re.sub(r'^\d{1,2}/\d{1,2}/\d{4}\s*', '', title).strip()
                    
                    if len(title) > 100:
                        break_patterns = [
                            r'(Chúng tôi)', r'(CTCP\s+[A-Z])', r'(NGÂN\s+HÀNG)', 
                            r'(TCT\s+[A-Z])', r'(Q[1-4]\.20\d{2},)', r'(TỔNG\s+CÔNG)',
                        ]
                        for pattern in break_patterns:
                            match = re.search(pattern, title, re.IGNORECASE)
                            if match and match.start() > 20:
                                title = title[:match.start()].strip()
                                break
                        else:
                            title = title[:100].strip()
                    
                    if not title or title in ['Xem ngay', '']: continue
                    
                    date_str = _extract_date_from_element(card)
                    
                    report_id_content = f"{title}|{detail_url}"
                    report_id = hashlib.md5(report_id_content.encode()).hexdigest()
                    
                    if report_id in existing_ids:
                        found_existing = True
                        continue
                    
                    ticker = extract_tickers(title)
                    print(f"  📎 Lấy PDF URL: {title[:50]}...")
                    pdf_url = _extract_pdf_url(session, detail_url)
                    
                    if not pdf_url:
                        print(f"  ⚠️ Không tìm thấy PDF cho: {title[:50]}")
                        continue
                    
                    all_reports.append({
                        'report_id': report_id,
                        'title': title,
                        'ticker': ticker,
                        'date': date_str,
                        'pdf_url': pdf_url,
                        'download_path': ''
                    })
                    new_in_page += 1
                    time.sleep(random.uniform(0.3, 0.8))
                except Exception as e:
                    print(f"  ⚠️ Lỗi xử lý item: {e}")
                    continue
            
            print(f"✅ Tìm thấy {new_in_page} báo cáo MỚI từ trang {page_num}")
            if new_in_page == 0 or (found_existing and new_in_page == 0):
                print("🛑 Dừng cào.")
                break
            
            page_num += 1
            if page_num % 5 == 0:
                time.sleep(random.uniform(2, 4))
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi khi cào trang {page_num}: {e}")
            break
    
    new_df = pd.DataFrame(all_reports)
    if len(new_df) > 0:
        final_df = pd.concat([new_df, old_df], ignore_index=True)
        print(f"\n🎉 Đã thêm {len(new_df)} báo cáo MỚI. Tổng: {len(final_df)} báo cáo.")
    else:
        final_df = old_df
        print(f"\n✨ Không có báo cáo mới. Tổng: {len(final_df)} báo cáo.")
    
    expected_columns = ['report_id', 'title', 'ticker', 'date', 'pdf_url', 'download_path']
    for col in expected_columns:
        if col not in final_df.columns:
            final_df[col] = ''
    final_df = final_df[expected_columns]
    
    scanner.save_csv(final_df)
    return final_df

if __name__ == "__main__":
    print("🚀 Starting ACBS Report Scraper...\n")
    df = run()
    print("\n✅ ACBS scan completed!")
