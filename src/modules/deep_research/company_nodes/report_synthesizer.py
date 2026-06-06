from src.modules.deep_research.company_state import CompanyState
from src.core.ai.tracker import call_llm_with_tracking

def synthesize_report(state: CompanyState):
    """
    Node 4: Tổng hợp mọi thứ thành Investment Memo (Màng lọc tinh hoa).
    """
    ticker = state["ticker"]
    print(f"\n--- Node 4: Synthesizing Final Report for {ticker} ---")
    
    profile = state.get("business_profile", {})
    finance = state.get("financial_insight", {})
    
    if profile.get("error") or finance.get("error"):
        print("Warning: Profile or Finance has error, memo might be incomplete.")

    print("Generating final Investment Memo with Google AI (Gemma 4)...")
    
    prompt = f"""
    Bạn là một Chuyên gia phân tích đầu tư cấp cao. Hãy tổng hợp thông tin sau đây về công ty {ticker} thành một bản Investment Memo chuyên nghiệp.
    
    TRIẾT LÝ: "The Filter" - Chỉ giữ lại những gì tinh túy nhất. Tuyệt đối không liệt kê lại số liệu thô nếu không đi kèm nhận định.
    
    DỮ LIỆU ĐẦU VÀO:
    1. Hồ sơ doanh nghiệp:
    {profile}
    
    2. Sức khỏe tài chính:
    {finance}
    
    YÊU CẦU CẤU TRÚC BÁO CÁO:
    - Sử dụng Markdown.
    - Phải có phần <think> (suy nghĩ nội bộ) để tranh biện về các dữ kiện trước khi đưa ra kết luận.
    - Đầu ra chính gồm:
        # INVESTMENT MEMO: {ticker}
        ## 1. Thesis (Luận điểm đầu tư cốt lõi)
        ## 2. Competitive Edge (Lợi thế cạnh tranh & Moat)
        ## 3. Financial Health (Sức khỏe tài chính & Rủi ro)
        ## 4. Final Verdict (Kết luận & Hành động gợi ý)
    """
    
    try:
        response_text, updated_state = call_llm_with_tracking(
            state=state,
            node_name="Node_4_Synthesizer",
            prompt=prompt,
            model_name="gemma-4-31b-it",
            json_mode=False
        )

        return {
            "final_memo": response_text,
            **updated_state
        }
    except Exception as e:
        print(f"Error in Node 4: {e}")
        error_msg = e.args[0] if len(e.args) > 0 else str(e)
        updated_state = e.args[1] if len(e.args) > 1 else state
        return {
            "final_memo": f"Lỗi khi tổng hợp báo cáo: {error_msg}",
            **updated_state
        }
