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
        f"Hãy trích xuất các thông tin quan trọng nhất từ nội dung sau đây liên quan đến chủ đề nghiên cứu: '{state['query']}'. "
        f"Trả về kết quả dưới dạng JSON với cấu trúc: "
        f"{{\"title\": \"Tiêu đề bài viết\", \"summary\": \"Tóm tắt nội dung chính (khoảng 200 chữ)\", \"key_facts\": [\"Sự thật 1\", \"Sự thật 2\"], \"sentiment\": \"Tích cực/Tiêu cực/Trung lập\"}}\n"
        f"Nội dung: {content[:15000]}"
    )
    
    try:
        response = client.models.generate_content(
            model=model, 
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        insight = json.loads(response.text)
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
    
    return {
        "current_content": insight.get("summary", ""),
        "current_title": insight.get("title", ""),
        "current_insight": insight
    }
