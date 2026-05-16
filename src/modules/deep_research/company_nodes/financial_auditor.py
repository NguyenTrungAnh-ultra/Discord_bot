import os
import json
from google import genai
from google.genai import types
from src.modules.deep_research.company_state import CompanyState
from src.utils.vci_client import get_financial_statement, format_financial_to_markdown
from src.utils.llm_utils import estimate_tokens, count_response_tokens

def audit_finances(state: CompanyState):
    """
    Node 2: Kéo dữ liệu BCTC từ VCI và phân tích sức khỏe tài chính.
    """
    ticker = state["ticker"]
    print(f"\n--- Node 2: Auditing Finances for {ticker} ---")

    try:
        print(f"Fetching real financial data for {ticker} from VCI...")
        fin_data = get_financial_statement(ticker)
        if not fin_data:
            print(f"No financial data found for {ticker}")
            return {"financial_data": None, "financial_insight": {"error": "No data found"}}

        markdown_fin = format_financial_to_markdown(fin_data)
        
        print("Analyzing financial health with Google AI (Gemma 4)...")
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        prompt = f"""
        Dưới đây là dữ liệu báo cáo tài chính của công ty {ticker} trong các kỳ gần nhất.
        Hãy phân tích sức khỏe tài chính và đưa ra các nhận xét quan trọng.
        Trả về kết quả dưới định dạng JSON duy nhất.
        
        Dữ liệu:
        {markdown_fin}
        
        Yêu cầu JSON format:
        {{
          "chain_of_thought": "Suy luận chi tiết về xu hướng doanh thu, lợi nhuận, nợ, dòng tiền...",
          "health_score": "Điểm số từ 1-10",
          "key_metrics": {{
             "gross_margin": "Giá trị biên lợi nhuận gộp gần nhất",
             "cfo": "Trạng thái dòng tiền từ HĐKD (Positive/Negative/Trend)",
             "debt_ratio": "Tỉ lệ nợ/Vốn chủ sở hữu hoặc nhận xét về nợ"
          }},
          "warnings": ["Các điểm rủi ro nếu có"]
        }}
        """
        
        # Khởi tạo counters
        current_input_tokens = state.get("total_input_tokens", 0)
        current_output_tokens = state.get("total_output_tokens", 0)
        current_requests = state.get("total_requests", 0)
        node_tokens = state.get("node_tokens", {})
        node_2_input = 0
        node_2_output = 0
        
        try:
            current_requests += 1
            input_tokens = estimate_tokens(prompt)
            current_input_tokens += input_tokens
            node_2_input += input_tokens

            response = client.models.generate_content(
                model="gemma-4-31b-it",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            output_tokens = count_response_tokens(response)
            current_output_tokens += output_tokens
            node_2_output += output_tokens
            
            fin_insight = json.loads(response.text)
            
            node_entry = node_tokens.get("Node_2_Finance", {"input": 0, "output": 0})
            node_tokens["Node_2_Finance"] = {
                "input": node_entry["input"] + node_2_input,
                "output": node_entry["output"] + node_2_output
            }
            
            return {
                "financial_data": {"status": "success", "periods_count": len(fin_data)},
                "financial_insight": fin_insight,
                "total_input_tokens": current_input_tokens,
                "total_output_tokens": current_output_tokens,
                "total_requests": current_requests,
                "node_tokens": node_tokens
            }
        except Exception as e:
            print(f"Error calling Google AI in Node 2: {e}")
            node_entry = node_tokens.get("Node_2_Finance", {"input": 0, "output": 0})
            node_tokens["Node_2_Finance"] = {
                "input": node_entry["input"] + node_2_input,
                "output": node_entry["output"] + node_2_output
            }
            return {
                "financial_data": None, 
                "financial_insight": {"error": f"LLM Error: {str(e)}"},
                "total_input_tokens": current_input_tokens,
                "total_output_tokens": current_output_tokens,
                "total_requests": current_requests,
                "node_tokens": node_tokens
            }
    except Exception as e:
        print(f"Error in Node 2: {e}")
        return {"financial_data": None, "financial_insight": {"error": str(e)}}
