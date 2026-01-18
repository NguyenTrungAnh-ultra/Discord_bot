import requests
from bs4 import BeautifulSoup
from src.utils.user_agent import get_random_desktop_user_agent
import pandas as pd
import time
import random
import os
import pickle

class Config:
    toan_canh_thi_truong_url = "https://kbsec.com.vn/vi/bao-cao-chien-luoc-thi-truong"
    bao_cao_cong_ty_url = "https://kbsec.com.vn/vi/bao-cao-cong-ty"
    bao_cao_nganh_url = "https://kbsec.com.vn/vi/bao-cao-ngan"
    bao_cao_vimo_url = "https://kbsec.com.vn/vi/bao-cao-trien-vong-kinh-te-vi-mo"
    bao_cao_chuyen_de_url = "https://kbsec.com.vn/vi/bao-cao-chuyen-de"


def run(toan_canh_thi_truong_url=False, 
                bao_cao_cong_ty_url=False, 
                bao_cao_nganh_url=False,
                bao_cao_vimo_url=False,
                bao_cao_chuyen_de=False):   
    # Đường dẫn file
    output_dir = r".\temp\reports"
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
    max_pages = 50  # Tăng lên để cào đủ nếu lần đầu
    found_existing = False  # Flag để dừng khi gặp báo cáo cũ
    
    while page_num <= max_pages:
        if page_num == 1:
            url = Config.bao_cao_cong_ty_url+".htm"
        else:
            url = f"{Config.bao_cao_cong_ty_url}/p-{page_num}.htm"
        
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
                    
                    # Nếu link là relative, thêm domain
                    if not pdf_url.startswith('http'):
                        pdf_url = f"https://kbsec.com.vn{pdf_url}"
                    
                    # Kiểm tra xem đã có trong DB cũ chưa
                    if pdf_url in existing_urls:
                        found_existing = True
                        continue  # Bỏ qua báo cáo đã có
                    
                    all_reports.append({
                        'title': title,
                        'pdf_url': pdf_url,
                        'page': page_num
                    })
                    new_in_page += 1
            
            print(f"✅ Tìm thấy {new_in_page} báo cáo MỚI từ trang {page_num}")
            
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


if __name__ == "__main__":
    run(bao_cao_cong_ty_url=True)
