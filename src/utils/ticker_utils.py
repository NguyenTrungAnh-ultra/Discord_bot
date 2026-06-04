import re

def extract_tickers(title: str) -> str:
    """
    Trích xuất mã cổ phiếu từ title
    - Trả về các mã cách nhau bằng dấu phẩy
    - Trả về None nếu không tìm thấy
    """
    excluded = {
        'CTCP', 'TCT', 'TNHH', 'ABB', 'CEO', 'CFO', 'COO', 'MUA', 'BAN', 'GIỮ',
        'KBSV', 'VND', 'USD', 'EUR', 'JPY', 'VNĐ', 'PDF', 'Q1', 'Q2', 'Q3', 'Q4',
        'FY', 'YTD', 'TTM', 'EPS', 'P/E', 'ROE', 'ROA', 'CAGR', 'EBITDA',
        'KHẢ', 'QUAN', 'CẬP', 'NHẬT', 'BAO', 'CAO', 'NHANH', 'KHÔNG', 'ĐÁNH', 'GIÁ',
        'CÔNG', 'TY', 'CỔ', 'PHẦN', 'NGÂN', 'HÀNG', 'TMCP', 'FTM', 'LNST', 'SVCK',
        'THU', 'GIAO', 'CHUY', 'HSX', 'HNX', 'UPCOM', 'VNIND', 'VNI', 'VN30',
        'TRU', 'TANG', 'GIAM', 'LOI', 'NHUAN', 'DOANH', 'THUE', 'QUY', 'NAM',
        'THANG', 'TUAN', 'NGAY'
    }
    
    tickers = re.findall(r'(?<![A-Za-z0-9])([A-Z]{3,4})(?![A-Za-z0-9])', title.upper())
    tickers = [t for t in tickers if t not in excluded]
    unique_tickers = sorted(set(tickers))
    
    if unique_tickers:
        return ','.join(unique_tickers)
    return None
