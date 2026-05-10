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
    model = "gemini-flash-latest"
    
    prompt = (
        f"Bạn là một chuyên gia phân tích dữ liệu. "
        f"Hãy trích xuất các thông tin quan trọng nhất từ nội dung sau đây liên quan đến chủ đề nghiên cứu: '{state['query']}'.\n\n"
        f"Yêu cầu tóm tắt theo phong cách: "
        f"1. Có tổng cộng bao nhiêu ý chính? "
        f"2. Những ý chính đó là gì? (Liệt kê ngắn gọn) "
        f"3. Nếu có lưu ý đặc biệt hoặc rủi ro gì thì đó là gì?\n\n"
        f"Trả về kết quả dưới dạng JSON với cấu trúc: "
        f"{{\"title\": \"Tiêu đề bài viết\", \"summary\": \"Đoạn tóm tắt tổng quan\", \"key_facts\": [\"Ý chính 1\", \"Ý chính 2\",...], \"notes\": [\"Lưu ý 1\", \"Lưu ý 2\",...], \"sentiment\": \"Tích cực/Tiêu cực/Trung lập\"}}\n"
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
