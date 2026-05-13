import os
import pandas as pd
from src.modules.deep_research.company_state import CompanyState

# Giả lập import từ folder VCI của bạn (Sẽ điều chỉnh path khi code thực tế)
# from No_need.BCTC.explorer.vci.financial1 import financial_statement

def audit_finances(state: CompanyState):
    """
    Node 2: Kéo dữ liệu BCTC từ VCI và phân tích sức khỏe tài chính.
    """
    ticker = state["ticker"]
    print(f"\n--- Node 2: Auditing Finances for {ticker} ---")

    # KỊCH BẢN TEST (MOCK)
    if state.get("is_mock"):
        print(f"[MOCK MODE] Đang giả lập dữ liệu tài chính cho {ticker}...")
        mock_fin_insight = {
            "chain_of_thought": "Dựa trên bảng cân đối giả lập, nợ đang giảm dần.",
            "health_score": "8/10",
            "key_metrics": {
                "gross_margin": "25%",
                "cfo": "Positive"
            }
        }
        return {
            "financial_data": {"status": "mock_data_loaded"}, 
            "financial_insight": mock_fin_insight
        }

    # LOGIC THỰC TẾ
    # 1. Gọi API Vietcap (VCI)
    # 2. Xử lý DataFrame
    # 3. Đưa vào LLM để nhận xét
    print("Logic thực tế (VCI API Integration) đang được xây dựng...")
    return {"financial_data": None, "financial_insight": None}
