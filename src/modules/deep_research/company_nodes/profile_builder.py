import json
from src.modules.deep_research.company_state import CompanyState
from src.modules.deep_research.tools.searxng_api import search_searxng
from src.modules.deep_research.tools.pdf_scraper import scrape_pdf
from src.core.ai.tracker import call_llm_with_tracking

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
    search_query = f"Báo cáo thường niên {ticker} filetype:pdf"
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
    
    prompt = f"""
    Dựa trên nội dung báo cáo sau đây của công ty {ticker}, hãy phân tích mô hình kinh doanh và lợi thế cạnh tranh.
    Trả về kết quả dưới định dạng JSON duy nhất.
    
    Nội dung:
    {pdf_content}
    
    Yêu cầu JSON format:
    {{
      "chain_of_thought": "Suy luận chi tiết về các điểm quan trọng",
      "report_date": "Ngày phát hành báo cáo được trích xuất từ tài liệu (định dạng dd/mm/yyyy, Q1/yyyy, Q2/yyyy, Q3/yyyy, Q4/yyyy, hoặc năm yyyy)",
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
    
    try:
        response_text, updated_state = call_llm_with_tracking(
            state=state,
            node_name="Node_1_Profile",
            prompt=prompt,
            model_name="gemma-4-31b-it",
            json_mode=True
        )
        
        profile_json = json.loads(response_text)
        profile_json["source_url"] = source_url
        
        return {
            "business_profile": profile_json,
            **updated_state
        }
    except Exception as e:
        print(f"Error calling Google AI in Node 1: {e}")
        error_msg = e.args[0] if len(e.args) > 0 else str(e)
        updated_state = e.args[1] if len(e.args) > 1 else state
        return {
            "business_profile": {"error": error_msg},
            **updated_state
        }
