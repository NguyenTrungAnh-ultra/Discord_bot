import requests
import pandas as pd
from datetime import date, timedelta, datetime
from core.utils.user_agent import get_headers
import time

def get_techcombank_rates(start_date, end_date):
    # Cấu hình headers (dựa trên thông tin bạn cung cấp)
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.7",
        "priority": "u=1, i",
        "referer": "https://techcombank.com/cong-cu-tien-ich/ty-gia",
        "sec-ch-ua": '"Brave";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "sec-gpc": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }

    data_list = []
    current_date = start_date
    
    print(f"Bắt đầu lấy dữ liệu từ {start_date} đến {end_date}...")

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        url = f"https://techcombank.com/content/techcombank/web/vn/vi/cong-cu-tien-ich/ty-gia/_jcr_content.exchange-rates.{date_str}.integration.json"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                json_data = response.json()
                
                # Kiểm tra cấu trúc JSON
                if 'exchangeRate' in json_data and 'data' in json_data['exchangeRate']:
                    items = json_data['exchangeRate']['data']
                    
                    if not items:
                        print(f"Ngày {date_str}: Không có dữ liệu")
                    else:
                        print(f"Ngày {date_str}: Lấy được {len(items)} bản ghi")
                        
                    for item in items:
                        # Lấy các cột yêu cầu
                        row = {
                            "Date": date_str,  # Thêm cột ngày để phân biệt
                            "sourceCurrency": item.get("sourceCurrency"),
                            "targetCurrency": item.get("targetCurrency"),
                            "askRate": item.get("askRate"),
                            "bidRateCK": item.get("bidRateCK")
                        }
                        data_list.append(row)
                else:
                    print(f"Ngày {date_str}: Cấu trúc dữ liệu không khớp")
            else:
                print(f"Ngày {date_str}: Lỗi request (Status {response.status_code})")
                
        except Exception as e:
            print(f"Ngày {date_str}: Có lỗi xảy ra - {e}")
        
        # Tăng ngày lên 1
        current_date += timedelta(days=1)
        # Nghỉ nhẹ để tránh spam server quá nhanh
        # time.sleep(0.1) 

    return data_list

# Thiết lập khoảng thời gian
start_d = date(2025, 1, 1)
end_d = datetime.now().date() # Lấy đến ngày hiện tại

# Chạy hàm lấy dữ liệu
all_rates = get_techcombank_rates(start_d, end_d)

if all_rates:
    # Tạo DataFrame
    df = pd.DataFrame(all_rates)
    
    # Sắp xếp lại cột cho đẹp
    cols = ["Date", "sourceCurrency", "targetCurrency", "askRate", "bidRateCK"]
    df = df[cols]
    
    # Xuất ra Excel
    output_file = "techcombank_ty_gia_2025.xlsx"
    df.to_excel(output_file, index=False)
    print(f"\nĐã xuất dữ liệu thành công ra file: {output_file}")
    print(df.head())
else:
    print("\nKhông lấy được dữ liệu nào.")