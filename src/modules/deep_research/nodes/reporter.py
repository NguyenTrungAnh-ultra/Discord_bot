import os
import re
from google import genai
from src.modules.deep_research.state import ResearchState

def report_node(state: ResearchState):
    """Generates the final research report based on collected insights."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    # Switched to gemini-flash-latest to avoid quota issues
    model = "gemma-4-26b-a4b-it"
    
    insights = state.get("insights", [])
    if not insights:
        return {"report": "Không có đủ dữ liệu để tạo báo cáo. Vui lòng kiểm tra lại kết nối mạng hoặc công cụ tìm kiếm."}

    insights_str = ""
    for i, insight in enumerate(insights):
        # Lấy URL từ insight (đã được lưu trong node storer trước đó)
        source_url = insight.get('url', 'Không rõ nguồn')
        insights_str += f"--- Nguồn {i+1}: {insight.get('title')} ---\n"
        insights_str += f"URL: {source_url}\n"
        insights_str += f"Tóm tắt: {insight.get('summary')}\n"
        insights_str += f"Các ý chính: {', '.join(insight.get('key_facts', []))}\n"
        # Bổ sung thêm phần lưu ý nếu có
        notes = insight.get('notes', [])
        if notes:
            insights_str += f"Lưu ý quan trọng: {', '.join(notes)}\n"
        insights_str += "\n"

    prompt = (
        f"Bạn là một Chuyên gia phân tích chiến lược vĩ mô (Deep Research AI). "
        f"Nhiệm vụ: Tổng hợp một Báo cáo Nghiên cứu Chuyên sâu bằng tiếng Việt về chủ đề: '{state['query']}' dựa trên các dữ kiện dưới đây.\n\n"
        f"QUAN TRỌNG - BẮT BUỘC SỬ DỤNG KỸ THUẬT SUY LUẬN BẬC CAO:\n"
        f"Trước khi viết báo cáo, bạn phải đặt toàn bộ quá trình tư duy vào cặp thẻ <think> và </think>. Bên trong thẻ này, bạn phải thực hiện tuần tự các bước sau (Prompt Chaining & Tree of Thought):\n"
        f"1. Khám phá dữ liệu (Exploration): Liệt kê các luồng thông tin chính. Xác định các số liệu cốt lõi và các điểm mâu thuẫn giữa các nguồn (nếu có).\n"
        f"2. Phân nhánh suy luận (Tree of Thought): Xây dựng 2-3 kịch bản khác nhau (ví dụ: Tích cực, Tiêu cực, Cơ sở) dựa trên các tác động vĩ mô (lãi suất, lạm phát, địa chính trị). Đánh giá xác suất và tính hợp lý của từng nhánh.\n"
        f"3. Hội tụ (Convergence): Chọn ra luận điểm cốt lõi (Core Thesis) vững chắc nhất dựa trên chất lượng nguồn và tính nhất quán của dữ liệu.\n"
        f"4. Lên khung logic (Structuring): Quyết định các ý chính sẽ đưa vào báo cáo để thuyết phục người đọc một cách logic nhất.\n\n"
        f"Cấu trúc của Báo cáo Nghiên cứu (phải nằm NGOÀI thẻ <think>):\n"
        f"1. Tóm tắt Thực thi (Executive Summary): Trình bày ngay luận điểm trung tâm, tác động cốt lõi và các con số đáng chú ý.\n"
        f"2. Bối cảnh Vĩ mô & Động lực chính (Macro & Key Drivers): Phân tích tác động của lãi suất, lạm phát, chuỗi cung ứng, và biến động vĩ mô.\n"
        f"3. Phân tích Ngành & Động thái Cạnh tranh: Những thay đổi lớn trong ngành, chiến lược của Key Players, và nút thắt thị trường.\n"
        f"4. Phân tích Kịch bản & Rủi ro (Scenario Analysis & Risks): Trình bày các kịch bản tương lai và đánh giá rủi ro từ dữ liệu thu thập được.\n"
        f"5. DANH SÁCH NGUỒN THAM KHẢO: Phải liệt kê kèm theo URL tương ứng từ các 'Nguồn' được cung cấp.\n\n"
        f"Yêu cầu chung:\n"
        f"- Văn phong học thuật, chuyên nghiệp, sắc bén và ngập tràn số liệu định lượng (nếu có).\n"
        f"- KHÔNG bịa đặt thông tin. Chỉ tổng hợp từ các 'Thông tin thu thập được' bên dưới.\n\n"
        f"Thông tin thu thập được:\n{insights_str}"
    )
    
    print("Generating final report...")
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        response_text = response.text
        
        # Extract and print chain of thought
        think_match = re.search(r'<think>(.*?)</think>', response_text, re.DOTALL)
        if think_match:
            thought_process = think_match.group(1).strip()
            print(f"\n🧠 [Chain of Thought - Reporter]:\n{thought_process}\n")
            # Remove the <think> block from the final report
            report = response_text.replace(think_match.group(0), "").strip()
        else:
            report = response_text.strip()
            
    except Exception as e:
        print(f"Error generating report: {e}")
        report = "Failed to generate report due to model error."

    return {"report": report}
