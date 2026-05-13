import os
import json
from src.modules.deep_research.company_state import CompanyState

def build_profile(state: CompanyState):
    """
    Node 1: Phân tích Mô hình kinh doanh và Lợi thế cạnh tranh.
    """
    ticker = state["ticker"]
    print(f"\n--- Node 1: Building Profile for {ticker} ---")

    # KỊCH BẢN TEST (MOCK) - Không tốn token
    if state.get("is_mock"):
        print(f"[MOCK MODE] Đang giả lập phân tích Profile cho {ticker}...")
        mock_insight = {
            "chain_of_thought": "Đây là dữ liệu giả lập để test luồng code.",
            "business_model": {
                "what_they_sell": f"Sản phẩm chủ lực của {ticker}",
                "revenue_streams": "Doanh thu đa dạng từ mảng A và B"
            },
            "economic_moat": {
                "moat_type": "Lợi thế quy mô",
                "strength": "High"
            }
        }
        return {"business_profile": mock_insight}

    # LOGIC THỰC TẾ (Sẽ code sau khi test luồng OK)
    # 1. Search Báo cáo thường niên/Bản cáo bạch
    # 2. Scrape nội dung
    # 3. Gọi LLM để bóc tách JSON
    print("Logic thực tế đang được xây dựng...")
    return {"business_profile": None}
