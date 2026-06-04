import json
from src.modules.deep_research.company_state import CompanyState
from src.utils.vci_client import get_financial_statement, format_financial_to_markdown
from src.utils.llm_utils import call_llm_with_tracking

def audit_finances(state: CompanyState):
    """
    Node 2: Kéo dữ liệu BCTC từ VCI và phân tích sức khỏe tài chính.
    """
    ticker = state["ticker"]
    print(f"\n--- Node 2: Auditing Finances for {ticker} ---")

    if state.get("financial_insight"):
        print(f"-> Financial Insight for {ticker} already exists in State. Skipping fetch and analysis.")
        return state

    try:
        print(f"Fetching real financial data for {ticker} from VCI...")
        fin_data = get_financial_statement(ticker)
        if not fin_data:
            print(f"No financial data found for {ticker}")
            return {"financial_data": None, "financial_insight": {"error": "No data found"}}

        markdown_fin = format_financial_to_markdown(fin_data)
        
        print("Analyzing financial health with Google AI (Gemma 4)...")
        
        prompt = f"""
        Dưới đây là dữ liệu báo cáo tài chính của công ty {ticker} trong các kỳ gần nhất.
        Hãy phân tích sức khỏe tài chính và đưa ra các nhận xét quan trọng.
        Trả về kết quả dưới định dạng JSON duy nhất.
        
        Dữ liệu:
        {markdown_fin}
        
        Yêu cầu JSON format:
        {{
          "chain_of_thought": "Suy luận chi tiết về xu hướng doanh thu, lợi nhuận, nợ, dòng tiền...",
          "report_date": "Ngày của kỳ báo cáo gần nhất trong dữ liệu (định dạng dd/mm/yyyy, Q1/2024, hoặc năm 2024)",
          "health_score": "Điểm số từ 1-10",
          "key_metrics": {{
             "gross_margin": "Giá trị biên lợi nhuận gộp gần nhất",
             "cfo": "Trạng thái dòng tiền từ HĐKD (Positive/Negative/Trend)",
             "debt_ratio": "Tỉ lệ nợ/Vốn chủ sở hữu hoặc nhận xét về nợ"
          }},
          "warnings": ["Các điểm rủi ro nếu có"]
        }}
        """
        
        try:
            response_text, updated_state = call_llm_with_tracking(
                state=state,
                node_name="Node_2_Finance",
                prompt=prompt,
                model_name="gemma-4-31b-it",
                json_mode=True
            )
            
            fin_insight = json.loads(response_text)
            
            return {
                "financial_data": {"status": "success", "periods_count": len(fin_data)},
                "financial_insight": fin_insight,
                **updated_state
            }
        except Exception as e:
            print(f"Error calling Google AI in Node 2: {e}")
            error_msg = e.args[0] if len(e.args) > 0 else str(e)
            updated_state = e.args[1] if len(e.args) > 1 else state
            return {
                "financial_data": None, 
                "financial_insight": {"error": error_msg},
                **updated_state
            }
    except Exception as e:
        print(f"Error in Node 2: {e}")
        return {"financial_data": None, "financial_insight": {"error": str(e)}}
