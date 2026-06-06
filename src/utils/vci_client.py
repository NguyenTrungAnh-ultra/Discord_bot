import json
import os
import pandas as pd
from src.core.scraper.http_client import send_request
from src.core.scraper.browser import get_headers

# --- CẤU HÌNH ---
REPORT_TYPES = ['BALANCE_SHEET', 'INCOME_STATEMENT', 'CASH_FLOW', 'NOTE']
HEADERS = get_headers(data_source='VCI')
PAYLOAD_JSON = {"query": "query Query {\n  ListFinancialRatio {\n    id\n    type\n    name\n    unit\n    isDefault\n    fieldName\n    en_Type\n    en_Name\n    tagName\n    comTypeCode\n    order\n    __typename\n  }\n}\n", "variables": {}}

def process_period_data(data_list):
    """
    Hàm xử lý dữ liệu (Years/Quarters): tạo code_name, transpose, set index.
    """
    if not data_list:
        return pd.DataFrame()

    df = pd.DataFrame(data_list)
    if 'yearReport' not in df.columns or 'lengthReport' not in df.columns:
        return pd.DataFrame()
        
    # Tạo định danh cột: Năm_Kỳ (vd: 2023_4)
    df['code_name'] = df['yearReport'].astype(str) + '_' + df['lengthReport'].astype(str)
    
    # Set index là code_name để khi Transpose nó trở thành Header cột
    df.set_index('code_name', inplace=True)
    
    # Transpose (Xoay trục): Hàng thành Cột
    df_transposed = df.T
    
    return df_transposed

def get_financial_statement(ticker: str):
    """
    Fetches financial statements for a given ticker from VCI.
    Returns a dictionary of DataFrames.
    """
    print(f"Fetching Metrics for {ticker}...")
    metrics_url = f'https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/financial-statement/metrics'
    metrics_response = send_request(
        url=metrics_url,
        headers=HEADERS,
        method="Get",
        payload=PAYLOAD_JSON
    )
    
    metrics_map = {}
    if metrics_response and 'data' in metrics_response:
        for r_type in REPORT_TYPES:
            metrics_map[r_type] = pd.DataFrame(metrics_response['data'].get(r_type, []))

    final_results = {}
    drop_cols = ['parent', 'titleEn', 'titleVi', 'field', 'name'] 

    for r_type in REPORT_TYPES:
        print(f"Processing {r_type} for {ticker}...")
        url = f'https://iq.vietcap.com.vn/api/iq-insight-service/v1/company/{ticker}/financial-statement?section={r_type}'
        
        response = send_request(
            url=url,
            headers=HEADERS,
            method="Get",
            payload=PAYLOAD_JSON
        )
        
        if not response or 'data' not in response:
            print(f"Warning: No data for {r_type}")
            continue

        metric_df = metrics_map.get(r_type)
        if metric_df is None or metric_df.empty:
            continue

        final_results[r_type] = {}
        for period in ['years', 'quarters']:
            raw_df = process_period_data(response['data'].get(period, []))
            if raw_df.empty:
                continue
                
            merged_df = pd.merge(
                metric_df,
                raw_df,
                left_on='field',
                right_index=True,
                how='left'
            )
            
            actual_drop = [c for c in drop_cols if c in merged_df.columns]
            merged_df.drop(columns=actual_drop, inplace=True)
            
            # Clean up: Rename 'tagName' to 'Metric' for readability if it exists
            if 'tagName' in merged_df.columns:
                merged_df.rename(columns={'tagName': 'Metric'}, inplace=True)
                
            final_results[r_type][period] = merged_df

    return final_results

def format_financial_to_markdown(financial_dict):
    """
    Converts the financial dictionary of DataFrames into a readable markdown string.
    """
    output = []
    for r_type, periods in financial_dict.items():
        output.append(f"### {r_type}")
        for period, df in periods.items():
            output.append(f"#### {period.capitalize()}")
            # Limit columns to last 4 periods to avoid huge text
            cols = df.columns.tolist()
            # Find which columns are the data columns (usually they look like 2023_4)
            data_cols = [c for c in cols if '_' in str(c) or str(c).isdigit()]
            other_cols = [c for c in cols if c not in data_cols]
            
            # Keep only the last 4 data columns
            display_data_cols = data_cols[-4:]
            display_cols = other_cols + display_data_cols
            
            # Filter: Remove rows where all display data columns are 0 or NaN
            filtered_df = df[display_cols].copy()
            # Check if all data cols are 0 or empty for each row
            numeric_data = filtered_df[display_data_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
            is_all_zero = (numeric_data == 0).all(axis=1)
            
            final_df = filtered_df[~is_all_zero]
            
            output.append(final_df.to_markdown(index=False))
            output.append("\n")
    return "\n".join(output)
