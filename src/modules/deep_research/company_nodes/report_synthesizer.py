import os
from google import genai
from google.genai import types
from src.modules.deep_research.company_state import CompanyState
from src.utils.llm_utils import estimate_tokens, count_response_tokens

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
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
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
    
    # Khởi tạo counters
    current_input_tokens = state.get("total_input_tokens", 0)
    current_output_tokens = state.get("total_output_tokens", 0)
    current_requests = state.get("total_requests", 0)
    node_tokens = state.get("node_tokens", {})
    node_4_input = 0
    node_4_output = 0
    
    try:
        current_requests += 1
        input_tokens = estimate_tokens(prompt)
        current_input_tokens += input_tokens
        node_4_input += input_tokens

        response = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=prompt
        )
        
        output_tokens = count_response_tokens(response)
        current_output_tokens += output_tokens
        node_4_output += output_tokens

        node_entry = node_tokens.get("Node_4_Synthesizer", {"input": 0, "output": 0})
        node_tokens["Node_4_Synthesizer"] = {
            "input": node_entry["input"] + node_4_input,
            "output": node_entry["output"] + node_4_output
        }

        return {
            "final_memo": response.text,
            "total_input_tokens": current_input_tokens,
            "total_output_tokens": current_output_tokens,
            "total_requests": current_requests,
            "node_tokens": node_tokens
        }
    except Exception as e:
        print(f"Error in Node 4: {e}")
        node_entry = node_tokens.get("Node_4_Synthesizer", {"input": 0, "output": 0})
        node_tokens["Node_4_Synthesizer"] = {
            "input": node_entry["input"] + node_4_input,
            "output": node_entry["output"] + node_4_output
        }
        return {
            "final_memo": f"Lỗi khi tổng hợp báo cáo: {e}",
            "total_input_tokens": current_input_tokens,
            "total_output_tokens": current_output_tokens,
            "total_requests": current_requests,
            "node_tokens": node_tokens
        }
