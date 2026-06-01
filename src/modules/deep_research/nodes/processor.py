import os
import gc
import json
from google import genai
from src.modules.deep_research.state import ResearchState
from src.modules.deep_research.tools.html_scraper import scrape_html
from src.modules.deep_research.tools.pdf_scraper import scrape_pdf

def process_node(state: ResearchState):
    """Scrapes the current URL and extracts insights using Gemini."""
    url = state.get("current_url")
    if not url:
        return {}

    print(f"--- Processing URL: {url} ---")
    
    content = None
    if url.lower().endswith(".pdf"):
        content = scrape_pdf(url)
    else:
        content = scrape_html(url)
    
    if not content:
        print(f"Failed to scrape content from {url}")
        return {"current_content": None, "current_title": "Failed to scrape", "current_insight": None}

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = "gemma-4-26b-a4b-it"
    
    prompt = (
        f"Bạn là một chuyên gia phân tích dữ liệu vĩ mô và tài chính (Deep Research AI). "
        f"Hãy đọc nội dung dưới đây và trích xuất các thông tin định lượng, góc nhìn vĩ mô quan trọng nhất liên quan đến chủ đề: '{state['query']}'.\n\n"
        f"Yêu cầu:\n"
        f"- Phân tích sâu: Chú trọng các con số cốt lõi (lãi suất, lạm phát, lợi nhuận), động thái của thị trường, sự gián đoạn chuỗi cung ứng, và rủi ro tiềm ẩn.\n"
        f"- Suy nghĩ trước (Chain of Thought): Đánh giá nhanh nguồn tin, tính xác thực của số liệu, và mức độ tác động vĩ mô của chúng trước khi tóm tắt.\n\n"
        f"Trả về MỘT OBJECT JSON DUY NHẤT với cấu trúc:\n"
        f"{{\n"
        f"  \"chain_of_thought\": \"Trình bày quá trình tư duy, đánh giá nguồn và ý nghĩa vĩ mô của dữ liệu...\",\n"
        f"  \"layer\": \"Phân loại: MACRO (Vĩ mô/Lãi suất/Chính sách) hoặc SECTOR (Ngành nghề) hoặc MICRO (Doanh nghiệp/Cổ phiếu)\",\n"
        f"  \"entities\": {{\"tickers\": [\"Mã CK/Tên cty\"], \"macro_factors\": [\"Chỉ số vĩ mô\"], \"publish_date\": \"Ngày đăng tải/xuất bản của bài viết hoặc báo cáo (định dạng dd/mm/yyyy, Q1/2024, hoặc năm 2024)\"}},\n"
        f"  \"title\": \"Tiêu đề bài viết (hoặc nội dung chính)\",\n"
        f"  \"summary\": \"Tóm tắt bản chất sự kiện (tập trung vào impact/tác động)\",\n"
        f"  \"key_facts\": [\"Ý chính 1 (ưu tiên có số liệu/bằng chứng)\", \"Ý chính 2\",...],\n"
        f"  \"notes\": [\"Rủi ro 1\", \"Góc khuất/Cảnh báo 2\",...],\n"
        f"  \"sentiment\": \"Tích cực/Tiêu cực/Trung lập\"\n"
        f"}}\n\n"
        f"Nội dung: {content[:30000]}"
    )
    
    try:
        print(f"🤖 AI is extracting insights from {url}...")
        response = client.models.generate_content(
            model=model, 
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        insight = json.loads(response.text)
        
        cot = insight.get("chain_of_thought", "")
        if cot:
            print(f"\n🧠 [Chain of Thought - Processor ({url})]:\n{cot}\n")
            
        print(f"✨ Successfully extracted insight: {insight.get('title')}")
    except Exception as e:
        print(f"Error extracting insight from {url}: {e}")
        insight = {
            "title": "Error", 
            "summary": "Không thể trích xuất thông tin.", 
            "key_facts": [], 
            "sentiment": "N/A"
        }

    # RAM Garbage Collection
    del content
    gc.collect()
    
    # Gán URL vào insight để phục vụ việc trích dẫn nguồn
    insight["url"] = url
    
    return {
        "current_content": insight.get("summary", ""),
        "current_title": insight.get("title", ""),
        "current_insight": insight
    }
