from typing import TypedDict, List, Dict, Any, Optional

class CompanyState(TypedDict):
    """
    Trạng thái lưu trữ dữ liệu của quy trình phân tích doanh nghiệp (Micro Research).
    """
    ticker: str                               # Mã chứng khoán cần phân tích (VD: HPG, FPT)
    
    # Dữ liệu từ Node 1: Profile Builder (Mô hình KD & Moat - Dữ liệu Tĩnh)
    business_profile: Optional[Dict[str, Any]] 
    
    # Dữ liệu từ Node 2: Financial Auditor (Tài chính & Lãnh đạo - Dữ liệu Động)
    financial_data: Optional[Dict[str, Any]]  # Raw dataframes hoặc JSON từ VCI API
    financial_insight: Optional[Dict[str, Any]] # Nhận xét của AI về tài chính
    
    # Kết quả cuối cùng
    final_memo: Optional[str]                 # Báo cáo Investment Memo
    
    # Kiểm soát luồng (Tùy chọn cho việc Mock hoặc Test)
    is_mock: bool                             # Nếu True, không gọi API LLM thực tế
