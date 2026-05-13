# Kế hoạch Triển khai Cơ chế Cache & Route cho Hệ thống Phân tích

Mục tiêu: Xây dựng cơ chế **"Check Database First"** để hệ thống không phải đi cào dữ liệu (scrape) và không phải gọi LLM phân tích lại nếu dữ liệu của quý/năm đó đã tồn tại trong PostgreSQL. Điều này giúp giảm 90% lượng Input Tokens và xử lý triệt để lỗi 500 do quá tải dữ liệu.

## Giai đoạn 1: Chuẩn bị các hàm giao tiếp Database
**File cần sửa:** `src/modules/deep_research/db/pgvector_db.py`
- Thêm phương thức `get_document_by_url(url: str)` vào class `VectorDatabase`.
- **Logic:** Query vào bảng `research_documents` với mệnh đề `WHERE url = %s`. Lấy ra trường `insight` (chứa dữ liệu JSON đã được LLM phân tích từ các lần chạy trước).

## Giai đoạn 2: Khởi tạo Node 0 - Cache Checker
**File mới:** `src/modules/deep_research/company_nodes/cache_checker.py`
- Xây dựng hàm `check_cache(state: CompanyState)`.
- **Logic:**
  1. Lấy `ticker` từ State.
  2. Xác định mốc thời gian hiện tại (Ví dụ: Năm 2024, Quý 1/2024).
  3. Query tìm Profile: `url = f"internal://company_profile/{ticker}"`.
  4. Query tìm Finance: `url = f"internal://financial_report/{ticker}/{current_year_quarter}"`.
  5. Nếu tìm thấy dữ liệu trong DB, bóc tách chuỗi JSON từ cột `insight` và đẩy thẳng vào `state["business_profile"]` hoặc `state["financial_insight"]`.
  6. Thêm cờ đánh dấu `state["_profile_from_cache"] = True` để thông báo cho các Node sau biết.
  7. Return state mới.

## Giai đoạn 3: Bổ sung Logic "Pass-through" (Đi thẳng) cho các Node Phân tích
Để tránh việc sửa đổi kiến trúc LangGraph quá phức tạp bằng Conditional Edges (Routing phức tạp), chúng ta sẽ áp dụng cơ chế "Bỏ qua nếu đã có dữ liệu" ngay đầu mỗi Node.

**File cần sửa:** `src/modules/deep_research/company_nodes/profile_builder.py`
- Ở dòng đầu tiên của hàm `build_profile`, thêm logic: 
  ```python
  if state.get("business_profile"):
      print("-> Dữ liệu Profile đã có sẵn từ Cache. Bỏ qua cào PDF và phân tích LLM.")
      return state # Trả lại state nguyên vẹn, không đếm token, không chạy LLM
  ```

**File cần sửa:** `src/modules/deep_research/company_nodes/financial_auditor.py`
- Tương tự, thêm logic ở đầu hàm:
  ```python
  if state.get("financial_insight"):
      print("-> Dữ liệu Tài chính đã có sẵn từ Cache. Bỏ qua cào VCI và phân tích LLM.")
      return state
  ```

**File cần sửa:** `src/modules/deep_research/company_nodes/company_storer.py`
- Thêm kiểm tra cờ ở Node 3. Nếu dữ liệu được lấy từ Cache ra, thì không cần chạy hàm Google Embedding và thao tác INSERT vào DB nữa (tránh gọi API thừa thãi).

## Giai đoạn 4: Cập nhật Cấu trúc LangGraph
**File cần sửa:** `src/modules/deep_research/company_graph.py`
- Import `cache_checker`.
- Thêm node: `workflow.add_node("cache_checker", check_cache)`.
- Sửa lại flow: 
  `START -> cache_checker -> profile_builder -> financial_auditor -> company_storer -> report_synthesizer -> END`.
- Luồng dữ liệu:
  - Cache Checker lấp đầy State bằng dữ liệu cũ (nếu có).
  - Builder & Auditor thấy State đã đầy -> Tự động Sleep (pass-through).
  - Storer thấy cờ cache -> Tự động Sleep.
  - Synthesizer -> Mặc định CÓ CHẠY để tổng hợp báo cáo mới tinh (chỉ tốn khoảng 1500 tokens input).

## Giai đoạn 5: Tối ưu hoá dữ liệu thô
**File cần sửa:** `src/utils/vci_client.py`
Để đề phòng trường hợp công ty đó CHƯA CÓ Cache và BẮT BUỘC phải cào mới, ta phải gọt bớt dữ liệu rác để tránh lỗi 500:
- Lọc bỏ các dòng chứa giá trị `0` toàn tập.
- Rút gọn số lượng chu kỳ cần hiển thị (ví dụ chỉ lấy 4 Quý gần nhất hoặc 2 Năm gần nhất) thay vì lấy quá sâu về quá khứ làm phình to Markdown.

---
**Tóm tắt lợi ích sau khi làm xong:**
1. Khi có người yêu cầu phân tích TCB (đã có trong DB), hệ thống mất **0 giây** cào dữ liệu, **0 token** Node 1, **0 token** Node 2. Chỉ mất duy nhất ~1500 token để Node 4 tổng hợp. Lỗi 500 sẽ gần như bằng 0.
2. Nếu mã chứng khoán mới toanh (như VNM), hệ thống tự động chạy quy trình cũ cào mạng, lưu vào DB, những người hỏi sau sẽ được hưởng lợi.
