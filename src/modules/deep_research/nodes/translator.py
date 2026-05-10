import os
from google import genai
from src.modules.deep_research.state import ResearchState

def translate_query(state: ResearchState):
    """Translates and optimizes the query for searching."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = "gemini-flash-latest"
    
    prompt = (
        f"Bạn là một chuyên gia nghiên cứu thị trường. "
        f"Tối ưu hóa truy vấn nghiên cứu sau đây thành danh sách các từ khóa tìm kiếm (bằng cả tiếng Việt và tiếng Anh) "
        f"để lấy được thông tin đa chiều nhất. "
        f"Chỉ trả về danh sách các câu truy vấn, mỗi câu trên một dòng. Không thêm lời chào hay giải thích.\n"
        f"Truy vấn: {state['query']}"
    )
    
    response = client.models.generate_content(model=model, contents=prompt)
    
    # Improved parsing: filter out lines that look like headers or conversational filler
    lines = response.text.strip().split("\n")
    queries = []
    for line in lines:
        clean = line.strip("- ").strip("* ").strip()
        if clean and len(clean) > 5 and not clean.lower().startswith("tiếng") and ":" not in clean:
            queries.append(clean)
    
    if not queries: # Fallback if parsing failed
        queries = [state['query']]
        
    return {
        "search_queries": queries[:10], # Limit to top 10 queries
        "iteration": 0,
        "urls": [],
        "insights": []
    }
