import os
import re
from google import genai
from src.modules.deep_research.state import ResearchState

def report_node(state: ResearchState):
    """Generates the final research report based on collected insights."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    # Switched to gemini-flash-latest to avoid quota issues
    model = "gemma-4-26b-a4b-it"
    
    from src.utils.date_parser import format_date_display

    insights = state.get("insights", [])
    if not insights:
        return {"report": "Không có đủ dữ liệu để tạo báo cáo. Vui lòng kiểm tra lại kết nối mạng hoặc công cụ tìm kiếm."}

    # 1. Build fresh scraped insights string
    insights_str = ""
    for i, insight in enumerate(insights):
        source_url = insight.get('url', 'Không rõ nguồn')
        
        # Extract publish date
        raw_date = None
        entities = insight.get("entities")
        if isinstance(entities, dict):
            raw_date = entities.get("publish_date") or entities.get("report_date")
        if not raw_date:
            raw_date = insight.get("publish_date") or insight.get("report_date")
            
        pub_date_display = format_date_display(raw_date) if raw_date else "Không rõ ngày"
        
        insights_str += f"--- Nguồn Mới {i+1}: {insight.get('title')} [Ngày đăng tải: {pub_date_display}] ---\n"
        insights_str += f"URL: {source_url}\n"
        insights_str += f"Tóm tắt: {insight.get('summary')}\n"
        insights_str += f"Các ý chính: {', '.join(insight.get('key_facts', []))}\n"
        
        notes = insight.get('notes', [])
        if notes:
            insights_str += f"Lưu ý quan trọng: {', '.join(notes)}\n"
        insights_str += "\n"

    # 2. Build db_insights (historical RAG) string
    db_insights = state.get("db_insights", []) or []
    db_insights_str = ""
    if db_insights:
        db_insights_str += "\n--- DỮ LIỆU LỊCH SỬ / HỒ SƠ CACHED TRONG DATABASE ---\n"
        for i, doc in enumerate(db_insights):
            pub_date_display = format_date_display(doc.get("publish_date"))
            source_url = doc.get('url', 'Không rõ nguồn')
            ticker_display = doc.get('ticker') or 'N/A'
            doc_type_display = doc.get('doc_type') or 'N/A'
            
            db_insights_str += f"--- Nguồn Lịch sử {i+1}: {doc.get('title')} [Ngày đăng tải: {pub_date_display}] [Ticker: {ticker_display}] [Loại tài liệu: {doc_type_display}] ---\n"
            db_insights_str += f"URL: {source_url}\n"
            db_insights_str += f"Nội dung/Tóm tắt: {doc.get('content')}\n"
            
            # Extract additional key facts/notes if insight dict is present
            doc_insight = doc.get("insight")
            if isinstance(doc_insight, dict):
                key_facts = doc_insight.get('key_facts', [])
                if key_facts:
                    db_insights_str += f"Các ý chính: {', '.join(key_facts)}\n"
                notes = doc_insight.get('notes', [])
                if notes:
                    db_insights_str += f"Lưu ý quan trọng: {', '.join(notes)}\n"
            db_insights_str += "\n"
    else:
        db_insights_str = "Không tìm thấy dữ liệu cũ liên quan trong database."

    prompt = (
        f"Bạn là một Chuyên gia phân tích chiến lược vĩ mô và phân tích tài chính (Deep Research AI).\n"
        f"Nhiệm vụ: Tổng hợp một Báo cáo Nghiên cứu Chuyên sâu bằng tiếng Việt về chủ đề: '{state['query']}' dựa trên các dữ kiện dưới đây.\n\n"
        f"QUAN TRỌNG - BẮT BUỘC SỬ DỤNG KỸ THUẬT SUY LUẬN BẬC CAO:\n"
        f"Trước khi viết báo cáo, bạn phải đặt toàn bộ quá trình tư duy vào cặp thẻ <think> và </think>. Bên trong thẻ này, bạn phải thực hiện tuần tự các bước sau (Prompt Chaining & Tree of Thought):\n"
        f"1. Khám phá dữ liệu (Exploration): Liệt kê các luồng thông tin mới và dữ liệu lịch sử từ DB. Xác định các số liệu cốt lõi và các điểm mâu thuẫn giữa các nguồn hoặc sự thay đổi theo thời gian (nếu có).\n"
        f"2. Phân nhánh suy luận (Tree of Thought): Xây dựng 2-3 kịch bản khác nhau (ví dụ: Tích cực, Tiêu cực, Cơ sở) dựa trên các tác động vĩ mô (lãi suất, lạm phát, địa chính trị). Đánh giá xác suất và tính hợp lý của từng nhánh.\n"
        f"3. Hội tụ (Convergence): Chọn ra luận điểm cốt lõi (Core Thesis) vững chắc nhất dựa trên chất lượng nguồn, tính nhất quán của dữ liệu mới và lịch sử.\n"
        f"4. Lên khung logic (Structuring): Quyết định các ý chính sẽ đưa vào báo cáo để thuyết phục người đọc một cách logic nhất.\n\n"
        f"ĐẶC BIỆT LƯU Ý VỀ NGÀY THÁNG DỮ LIỆU:\n"
        f"- Đối với mỗi thông tin được đưa vào báo cáo, hãy chú ý đến 'Ngày đăng tải' đi kèm với nguồn đó để đảm bảo tính thời sự và phân tích sự thay đổi theo thời gian.\n"
        f"- Khi phân tích các biến số vĩ mô hoặc số liệu tài chính doanh nghiệp, bạn PHẢI nêu rõ ngày tháng công bố hoặc thời điểm của dữ liệu (ví dụ: 'Tại ngày dd/mm/yyyy...', 'Theo số liệu công bố quý Q3/2024...', v.v.) để người đọc biết được thông tin đó là mới hay cũ.\n"
        f"- Trong phần 5. DANH SÁCH NGUỒN THAM KHẢO, hãy liệt kê đầy đủ nguồn bao gồm: [Tiêu đề](URL) - Ngày đăng tải: dd/mm/yyyy.\n\n"
        f"Cấu trúc của Báo cáo Nghiên cứu (phải nằm NGOÀI thẻ <think>):\n"
        f"1. Tóm tắt Thực thi (Executive Summary): Trình bày ngay luận điểm trung tâm, tác động cốt lõi và các con số đáng chú ý.\n"
        f"2. Bối cảnh Vĩ mô & Động lực chính (Macro & Key Drivers): Phân tích tác động của lãi suất, lạm phát, chuỗi cung ứng, và biến động vĩ mô.\n"
        f"3. Phân tích Ngành & Động thái Cạnh tranh: Những thay đổi lớn trong ngành, chiến lược của Key Players, và nút thắt thị trường.\n"
        f"4. Phân tích Kịch bản & Rủi ro (Scenario Analysis & Risks): Trình bày các kịch bản tương lai và đánh giá rủi ro từ dữ liệu thu thập được.\n"
        f"5. DANH SÁCH NGUỒN THAM KHẢO: Phải liệt kê kèm theo URL tương ứng từ các nguồn mới và nguồn lịch sử.\n\n"
        f"Yêu cầu chung:\n"
        f"- Văn phong học thuật, chuyên nghiệp, sắc bén và ngập tràn số liệu định lượng (nếu có).\n"
        f"- KHÔNG bịa đặt thông tin. Chỉ tổng hợp từ các thông tin được cung cấp bên dưới.\n\n"
        f"DỮ LIỆU ĐẦU VÀO:\n"
        f"--- THÔNG TIN MỚI THU THẬP ---\n{insights_str}\n"
        f"--- THÔNG TIN LỊCH SỬ TỪ RAG DB ---\n{db_insights_str}\n"
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
