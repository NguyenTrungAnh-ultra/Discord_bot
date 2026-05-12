import os
import re
from google import genai
from src.modules.deep_research.state import ResearchState

def translate_query(state: ResearchState):
    """Translates and optimizes the query for searching."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = "gemini-flash-latest"
    
    prompt = (
        f"Bạn là một hệ thống AI nghiên cứu chuyên sâu (Deep Research API) tương tự Perplexity. "
        f"Nhiệm vụ của bạn là phân tích và chia nhỏ truy vấn cốt lõi: '{state['query']}' thành một danh sách các câu lệnh tìm kiếm chiến lược (tiếng Anh và tiếng Việt).\n\n"
        f"QUAN TRỌNG: Hãy trình bày quá trình tư duy (Chain of Thought) của bạn trước khi tạo truy vấn. Đặt toàn bộ quá trình suy nghĩ phân tích vào trong cặp thẻ <think> và </think>.\n\n"
        f"Các câu lệnh tìm kiếm phải xoáy sâu vào các yếu tố tác động mạnh nhất, đặc biệt là các biến số vĩ mô toàn cầu, theo cấu trúc sau:\n"
        f"1. Dữ liệu Vĩ mô & Sự kiện Toàn cầu: Động thái lãi suất (FED/ECB), lạm phát, tỷ giá, chính sách tiền tệ, và biến động giá hàng hóa cốt lõi (dầu mỏ, vàng, năng lượng).\n"
        f"2. Phân tích Ngành & Chuỗi cung ứng: Quy mô thị trường, các nút thắt chuỗi cung ứng (bottlenecks), chi phí đầu vào, và tác động của địa chính trị.\n"
        f"3. Động lực Cạnh tranh & Đổi mới: Động thái của các doanh nghiệp dẫn đầu (Key Players), sự kiện M&A, và công nghệ mới định hình lại ngành.\n"
        f"4. Rủi ro & Dự báo Tương lai: Đánh giá, số liệu định lượng từ các tổ chức uy tín (IMF, World Bank, Bloomberg, Reuters, Morgan Stanley...), và rủi ro tiềm ẩn.\n\n"
        f"Yêu cầu:\n"
        f"- Tạo ra từ 6-10 truy vấn đặc thù, bao quát các khía cạnh vĩ mô và vi mô ở trên.\n"
        f"- Sử dụng các từ khóa nâng cao (ví dụ: 'macroeconomic impact', 'interest rate correlation', 'supply chain disruption', 'market forecast', 'yield curve').\n"
        f"- Ưu tiên sử dụng tiếng Anh để tiếp cận các báo cáo nghiên cứu toàn cầu chất lượng cao, kết hợp tiếng Việt cho các yếu tố mang tính địa phương.\n"
        f"- Tuyệt đối KHÔNG tìm kiếm trên mạng xã hội (loại bỏ Facebook, Twitter, Reddit, TikTok...). Chỉ tập trung vào báo cáo ngành, tin tức tài chính, và số liệu định lượng.\n"
        f"- Phần danh sách truy vấn phải NẰM NGOÀI thẻ <think>. Mỗi câu trên một dòng, không thêm bất kỳ lời giải thích nào khác.\n"
    )
    
    response = client.models.generate_content(model=model, contents=prompt)
    response_text = response.text
    
    # Extract and print chain of thought
    think_match = re.search(r'<think>(.*?)</think>', response_text, re.DOTALL)
    if think_match:
        thought_process = think_match.group(1).strip()
        print(f"\n🧠 [Chain of Thought - Translator]:\n{thought_process}\n")
        response_text = response_text.replace(think_match.group(0), "").strip()
    
    # Improved parsing: filter out lines that look like headers or conversational filler
    lines = response_text.strip().split("\n")
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
