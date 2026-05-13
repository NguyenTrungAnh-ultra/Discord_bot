from src.modules.deep_research.company_state import CompanyState

def synthesize_report(state: CompanyState):
    """
    Node 4: Tổng hợp mọi thứ thành Investment Memo (Màng lọc tinh hoa).
    """
    ticker = state["ticker"]
    print(f"\n--- Node 4: Synthesizing Final Report for {ticker} ---")

    # KỊCH BẢN TEST (MOCK)
    if state.get("is_mock"):
        print(f"[MOCK MODE] Đang tạo báo cáo mẫu...")
        final_memo = f"""
# INVESTMENT MEMO: {ticker}
## 1. Mô hình kinh doanh
Dữ liệu giả lập: Công ty hàng đầu trong lĩnh vực công nghệ.

## 2. Sức khỏe tài chính
Dữ liệu giả lập: Tài chính lành mạnh, dòng tiền dương.

## 3. Kết luận
Đáng chú ý để theo dõi.
        """
        return {"final_memo": final_memo}

    # LOGIC THỰC TẾ
    # 1. Gộp toàn bộ State
    # 2. Ép LLM dùng <think> để lọc dữ liệu
    # 3. Trả ra bản Memo tinh gọn
    print("Logic thực tế (The Filter) đang được xây dựng...")
    return {"final_memo": "Báo cáo thực tế chưa được tạo."}
