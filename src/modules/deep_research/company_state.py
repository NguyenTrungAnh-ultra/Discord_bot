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
    
    # Theo dõi tài nguyên
    total_input_tokens: int                   # Tổng số token đầu vào
    total_output_tokens: int                  # Tổng số token đầu ra
    total_requests: int                       # Tổng số request đã gửi (LLM + Embedding)
    node_tokens: dict                         # Đếm token chi tiết cho từng node
    _profile_from_cache: Optional[bool]       # Cờ đánh dấu dữ liệu lấy từ cache
