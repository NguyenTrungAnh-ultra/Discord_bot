# Kế Hoạch Triển Khai - Hệ Thống Deep Research (LangGraph + Gemini + pgvector)

## Mục tiêu
Xây dựng một module nghiên cứu độc lập `deep_research` có khả năng tự động tìm kiếm, cào dữ liệu HTML/PDF, và trích xuất/lưu trữ vector vào PostgreSQL, cuối cùng sinh ra báo cáo phân tích.

## Nguyên tắc Thiết kế
1. **Tuần tự & Garbage Collection:** Đọc từng URL, xử lý và xóa biến ngay (dùng `del` và `gc.collect()`) để tránh rò rỉ RAM, phù hợp cho môi trường có 16GB RAM nhưng cần chạy bền bỉ.
2. **Môi trường Test Độc lập:** Tách luồng này ra khỏi `main.py` của bot (chạy qua file test `run_test_research.py` trước), giúp dễ debug LangGraph.
3. **Kế thừa Core:** Tái sử dụng `src/core/db.py` và `src/core/gg_service.py` hiện tại.

## Chi tiết các Chặng (Phases)

### Chặng 1: Kết nối Vector Database (`pgvector`)
- **Mục tiêu:** Cài đặt Extension `vector`, tạo schema lưu trữ tài liệu đã cào, thiết lập kết nối có hỗ trợ `pgvector`.
- **Files cần tạo/sửa:**
  - `src/modules/deep_research/db/schema.sql`: Khởi tạo bảng `research_documents`.
  - `src/modules/deep_research/db/pgvector_db.py`: Cấu hình kết nối và register type `pgvector` vào connection (thừa kế hoặc bọc lại `Database` từ `src/core/db.py`).

### Chặng 2: Bộ Công cụ Scraper (Tools)
- **Mục tiêu:** Xây dựng các Tools để lấy URL và parse nội dung (HTML, PDF).
- **Files cần tạo/sửa:**
  - `src/modules/deep_research/tools/searxng_api.py`: Hàm gọi Local SearxNG API để lấy danh sách URL.
  - `src/modules/deep_research/tools/html_scraper.py`: Xử lý HTML thành Text bằng `trafilatura`.
  - `src/modules/deep_research/tools/pdf_scraper.py`: Xử lý PDF thành Text bằng `PyMuPDF`.

### Chặng 3: Định nghĩa LangGraph (State & Nodes)
- **Mục tiêu:** Cài đặt TypedDict `State` lưu trạng thái của Graph và triển khai logic cho từng Node xử lý.
- **Files cần tạo/sửa:**
  - `src/modules/deep_research/state.py`: Định nghĩa `ResearchState`.
  - `src/modules/deep_research/nodes/translator.py`: (Node 1) Dùng Gemini Flash dịch truy vấn ra từ khóa search.
  - `src/modules/deep_research/nodes/searcher.py`: (Node 2) Gọi SearxNG Tools cập nhật list URL.
  - `src/modules/deep_research/nodes/dispatcher.py`: (Node 3) Pop URL, gán vào URL hiện tại.
  - `src/modules/deep_research/nodes/processor.py`: (Node 5) Dùng Gemini Flash ép chuẩn JSON (trích xuất insight thô).
  - `src/modules/deep_research/nodes/storer.py`: (Node 6) Gọi Embedding, lưu vào Postgres pgvector, ép dọn rác RAM.
  - `src/modules/deep_research/nodes/reporter.py`: (Node 7) Dùng Gemini Pro query vector db, sinh báo cáo PESTLE/Porter.

### Chặng 4: Vẽ Đồ thị Workflow & Chạy thử
- **Mục tiêu:** Định nghĩa workflow qua LangGraph, kết nối các Edge (đặc biệt là vòng lặp dispatcher <-> storer) và viết script chạy thử nghiệm.
- **Files cần tạo/sửa:**
  - `src/modules/deep_research/main_graph.py`: Xâu chuỗi Nodes, tạo compiled Graph.
  - `run_test_research.py` (Thư mục root): Khởi chạy đồ thị với một `query` cứng để test luồng từ đầu đến cuối.
