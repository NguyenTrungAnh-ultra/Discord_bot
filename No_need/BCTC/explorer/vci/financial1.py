"""
Module quản lý thông tin báo cáo tài chính từ nguồn dữ liệu VCI.
Optimized version.
"""

import json
import os
import pandas as pd
from core.utils import client
from core.utils.user_agent import get_headers

# --- CẤU HÌNH ---
TICKER = "TCB"
DATA_DIR = "./data"
REPORT_TYPES = ['BALANCE_SHEET', 'INCOME_STATEMENT', 'CASH_FLOW', 'NOTE']

# Đảm bảo thư mục tồn tại
os.makedirs(DATA_DIR, exist_ok=True)

# Payload cho API (nếu cần dùng cho POST/GET body)
PAYLOAD_STR = "{\"query\":\"query Query {\\n  ListFinancialRatio {\\n    id\\n    type\\n    name\\n    unit\\n    isDefault\\n    fieldName\\n    en_Type\\n    en_Name\\n    tagName\\n    comTypeCode\\n    order\\n    __typename\\n  }\\n}\\n\",\"variables\":{}}"
PAYLOAD_JSON = json.loads(PAYLOAD_STR)

HEADERS = get_headers(data_source='VCI')

def process_period_data(data_list):
    """
    Hàm xử lý dữ liệu (Years/Quarters): tạo code_name, transpose, set index.
    """
    if not data_list:
        return pd.DataFrame()

    df = pd.DataFrame(data_list)
    
    # Tạo định danh cột: Năm_Kỳ (vd: 2023_4)
    df['code_name'] = df['yearReport'].astype(str) + '_' + df['lengthReport'].astype(str)
    
    # Set index là code_name để khi Transpose nó trở thành Header cột
    df.set_index('code_name', inplace=True)
    
    # Transpose (Xoay trục): Hàng thành Cột
    df_transposed = df.T
    
    return df_transposed

def financial_statement():
    # 1. Lấy dữ liệu Metrics (Định nghĩa các chỉ số)
    # ---------------------------------------------------------
    print("Fetching Metrics...")
    metrics_url = 'https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/TCB/financial-statement/metrics'
    metrics_response = client.send_request(
        url=metrics_url,
        headers=HEADERS,
        method="Get",
        payload=PAYLOAD_JSON
    )
    
    # Lưu metrics vào dict để tra cứu nhanh
    metrics_map = {}
    if metrics_response and 'data' in metrics_response:
        for r_type in REPORT_TYPES:
            metrics_map[r_type] = pd.DataFrame(metrics_response['data'].get(r_type, []))

    # Dictionary chứa kết quả cuối cùng
    final_results = {}

    # Các cột cần loại bỏ sau khi merge
    drop_cols = ['parent', 'titleEn', 'titleVi', 'field', 'name'] 
    # Lưu ý: 'Unnamed: 0' không còn xuất hiện vì không đọc từ CSV

    # 2. Lấy dữ liệu Financial Statement và Xử lý
    # ---------------------------------------------------------
    for r_type in REPORT_TYPES:
        print(f"Processing {r_type}...")
        
        # Tạo URL dynamic
        url = f'https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{TICKER}/financial-statement?section={r_type}'
        
        response = client.send_request(
            url=url,
            headers=HEADERS,
            method="Get",
            payload=PAYLOAD_JSON
        )
        
        if not response or 'data' not in response:
            print(f"Warning: No data for {r_type}")
            continue

        # Lấy DataFrame Metric tương ứng
        metric_df = metrics_map.get(r_type)

        # Xử lý cho cả Years và Quarters
        final_results[r_type] = {}
        
        for period in ['years', 'quarters']:
            # Xử lý dữ liệu thô (transpose, set index)
            raw_df = process_period_data(response['data'].get(period, []))
            
            # Merge: metric_df (cột 'field') khớp với raw_df (index - vì đã transpose)
            # left_on='field', right_index=True
            merged_df = pd.merge(
                metric_df,
                raw_df,
                left_on='field',
                right_index=True,
                how='left'
            )
            
            # Làm sạch columns
            # Chỉ drop những cột tồn tại trong df
            actual_drop = [c for c in drop_cols if c in merged_df.columns]
            merged_df.drop(columns=actual_drop, inplace=True)
            
            # Lưu vào dict kết quả
            final_results[r_type][period] = merged_df
            
            # (Tùy chọn) Lưu file CSV kết quả cuối cùng nếu cần kiểm tra
            merged_df.to_csv(f"{DATA_DIR}/{r_type}_{period}_final.csv", index=False)

    # 3. Gán ra biến riêng lẻ như yêu cầu cũ (Unpacking)
    # ---------------------------------------------------------
    # Để tương thích với phần code phía sau của bạn (nếu có)
    bs_q = final_results['BALANCE_SHEET']['quarters']
    bs_y = final_results['BALANCE_SHEET']['years']
    
    is_q = final_results['INCOME_STATEMENT']['quarters']
    is_y = final_results['INCOME_STATEMENT']['years']
    
    cf_q = final_results['CASH_FLOW']['quarters']
    cf_y = final_results['CASH_FLOW']['years']
    
    note_q = final_results['NOTE']['quarters']
    note_y = final_results['NOTE']['years']

    # Kiểm tra thử
    print("-" * 30)
    print("Kích thước bs_q:", bs_q.shape)
    print("Các cột của bs_q (5 cột đầu):", bs_q.columns.tolist()[:5])

if __name__ == "__main__":
    financial_statement()