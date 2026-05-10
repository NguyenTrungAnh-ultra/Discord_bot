import os
from google import genai
from src.modules.deep_research.state import ResearchState

def translate_query(state: ResearchState):
    """Translates and optimizes the query for searching."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = "gemini-flash-latest"
    
    prompt = (
        f"Bạn là một chuyên gia nghiên cứu thị trường cao cấp. "
        f"Nhiệm vụ của bạn là tối ưu hóa truy vấn nghiên cứu: '{state['query']}' thành một danh sách các câu lệnh tìm kiếm (tiếng Việt và tiếng Anh).\n\n"
        f"Các câu lệnh tìm kiếm phải tập trung thu thập dữ liệu để phục vụ việc viết báo cáo theo cấu trúc:\n"
        f"1. Tổng quan và quy mô thị trường.\n"
        f"2. Phân tích PESTLE (Chính trị, Kinh tế, Xã hội, Công nghệ, Pháp lý, Môi trường).\n"
        f"3. Phân tích 5 áp lực cạnh tranh của Porter.\n"
        f"4. Xu hướng và dự báo tương lai.\n\n"
        f"Yêu cầu:\n"
        f"- Tạo ra từ 5-8 truy vấn đa chiều, bao quát các khía cạnh trên.\n"
        f"- Kết hợp cả tiếng Việt và tiếng Anh để lấy dữ liệu từ các nguồn uy tín toàn cầu.\n"
        f"- Chỉ trả về danh sách các câu truy vấn, mỗi câu trên một dòng. Không thêm lời chào hay giải thích.\n"
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
        print("⚠️ Warning: Could not parse queries, using original query.")
        queries = [state['query']]
    
    print(f"✅ Generated {len(queries)} search queries.")
        
    return {
        "search_queries": queries[:10], # Limit to top 10 queries
        "iteration": 0,
        "urls": [],
        "insights": []
    }
