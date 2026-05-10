import os
from google import genai
from src.modules.deep_research.state import ResearchState

def report_node(state: ResearchState):
    """Generates the final research report based on collected insights."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    # Switched to gemini-flash-latest to avoid quota issues
    model = "gemini-flash-latest"
    
    insights = state.get("insights", [])
    if not insights:
        return {"report": "Không có đủ dữ liệu để tạo báo cáo. Vui lòng kiểm tra lại kết nối mạng hoặc công cụ tìm kiếm."}

    insights_str = ""
    for i, insight in enumerate(insights):
        insights_str += f"--- Nguồn {i+1}: {insight.get('title')} ---\n"
        insights_str += f"Tóm tắt: {insight.get('summary')}\n"
        insights_str += f"Sự thật: {', '.join(insight.get('key_facts', []))}\n\n"

    prompt = (
        f"Bạn là một chuyên gia nghiên cứu thị trường cao cấp. "
        f"Dựa trên các thông tin đã thu thập dưới đây, hãy viết một báo cáo nghiên cứu chi tiết bằng tiếng Việt về chủ đề: '{state['query']}'.\n"
        f"Yêu cầu báo cáo bao gồm:\n"
        f"1. Tổng quan thị trường.\n"
        f"2. Phân tích PESTLE (Chính trị, Kinh tế, Xã hội, Công nghệ, Pháp lý, Môi trường) nếu phù hợp.\n"
        f"3. Phân tích 5 áp lực cạnh tranh của Porter.\n"
        f"4. Kết luận và đề xuất.\n\n"
        f"Thông tin thu thập được:\n{insights_str}"
    )
    
    print("Generating final report...")
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        report = response.text
    except Exception as e:
        print(f"Error generating report: {e}")
        report = "Failed to generate report due to model error."

    return {"report": report}
