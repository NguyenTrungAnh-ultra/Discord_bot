import os
import json
from google import genai
from google.genai import types
from src.modules.deep_research.company_state import CompanyState
from src.modules.deep_research.tools.searxng_api import search_searxng
from src.modules.deep_research.tools.pdf_scraper import scrape_pdf
from src.utils.llm_utils import estimate_tokens, count_response_tokens

def build_profile(state: CompanyState):
    """
    Node 1: Phân tích Mô hình kinh doanh và Lợi thế cạnh tranh.
    """
    ticker = state["ticker"]
    print(f"\n--- Node 1: Building Profile for {ticker} ---")
    
    if state.get("business_profile"):
        print(f"-> Business Profile for {ticker} already exists in State. Skipping scraping and analysis.")
        return state
    
    print(f"Searching for annual reports/prospectus for {ticker}...")
    search_query = f"Báo cáo thường niên {ticker} 2024 filetype:pdf"
    search_results = search_searxng(search_query, num_results=3)
    
    if not search_results:
        print("No search results found. Trying broader search...")
        search_query = f"Bản cáo bạch {ticker} filetype:pdf"
        search_results = search_searxng(search_query, num_results=3)

    pdf_content = ""
    source_url = ""
    for res in search_results:
        print(f"Attempting to scrape: {res['url']}")
        content = scrape_pdf(res['url'])
        if content and len(content) > 1000:
            pdf_content = content[:50000] # Limit to 50k chars for prompt
            source_url = res['url']
            break
    
    if not pdf_content:
        print("Could not retrieve enough content from PDFs.")
        return {"business_profile": {"error": "No content found"}}

    print("Analyzing business profile with Google AI (Gemma 4)...")
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    prompt = f"""
    Dựa trên nội dung báo cáo sau đây của công ty {ticker}, hãy phân tích mô hình kinh doanh và lợi thế cạnh tranh.
    Trả về kết quả dưới định dạng JSON duy nhất.
    
    Nội dung:
    {pdf_content}
    
    Yêu cầu JSON format:
    {{
      "chain_of_thought": "Suy luận chi tiết về các điểm quan trọng",
      "report_date": "Ngày phát hành báo cáo được trích xuất từ tài liệu (định dạng dd/mm/yyyy, Q1/2024, hoặc năm 2024)",
      "business_model": {{
         "what_they_sell": "Mô tả sản phẩm/dịch vụ",
         "target_customers": "Đối tượng khách hàng chính",
         "revenue_streams": "Các nguồn doanh thu chính"
      }},
      "economic_moat": {{
         "moat_type": "Loại lợi thế cạnh tranh (vd: Lợi thế quy mô, Chi phí chuyển đổi, Thương hiệu...)",
         "strength": "High/Medium/Low",
         "evidence": "Bằng chứng từ báo cáo"
      }}
    }}
    """
    
    # Khởi tạo counters nếu chưa có
    current_input_tokens = state.get("total_input_tokens", 0)
    current_output_tokens = state.get("total_output_tokens", 0)
    current_requests = state.get("total_requests", 0)
    node_tokens = state.get("node_tokens", {})
    node_1_input = 0
    node_1_output = 0

    try:
        current_requests += 1
        input_tokens = estimate_tokens(prompt)
        current_input_tokens += input_tokens
        node_1_input += input_tokens
        
        response = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        output_tokens = count_response_tokens(response)
        current_output_tokens += output_tokens
        node_1_output += output_tokens
        
        profile_json = json.loads(response.text)
        profile_json["source_url"] = source_url
        
        node_entry = node_tokens.get("Node_1_Profile", {"input": 0, "output": 0})
        node_tokens["Node_1_Profile"] = {
            "input": node_entry["input"] + node_1_input,
            "output": node_entry["output"] + node_1_output
        }
        
        return {
            "business_profile": profile_json,
            "total_input_tokens": current_input_tokens,
            "total_output_tokens": current_output_tokens,
            "total_requests": current_requests,
            "node_tokens": node_tokens
        }
    except Exception as e:
        print(f"Error calling Google AI in Node 1: {e}")
        node_entry = node_tokens.get("Node_1_Profile", {"input": 0, "output": 0})
        node_tokens["Node_1_Profile"] = {
            "input": node_entry["input"] + node_1_input,
            "output": node_entry["output"] + node_1_output
        }
        return {
            "business_profile": {"error": f"LLM Error: {str(e)}"},
            "total_input_tokens": current_input_tokens,
            "total_output_tokens": current_output_tokens,
            "total_requests": current_requests,
            "node_tokens": node_tokens
        }
