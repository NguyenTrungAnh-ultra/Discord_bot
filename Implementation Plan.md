# Kế hoạch Tái cấu trúc Dự án (Architecture Refactoring Plan)

Dựa trên phân tích mã nguồn và cấu trúc hiện tại, hệ thống này đã vượt quá khuôn khổ của một "Discord Bot" đơn giản và trở thành một nền tảng RAG Agent phức tạp. Do đó, kiến trúc cần được tái cấu trúc (refactor) để phân tách rõ ràng trách nhiệm giữa **Core (Hạ tầng nền tảng)**, **Modules (Luồng nghiệp vụ)** và **Utils (Công cụ tiện ích)**.

> [!WARNING]
> Việc di chuyển các file sẽ yêu cầu cập nhật hàng loạt các đường dẫn import (ví dụ: `from src.utils.llm_utils` thành `from src.core.ai.tracker`). Việc này phải được thực hiện đồng bộ trên tất cả các file để tránh lỗi `ModuleNotFoundError`.

---

## Proposed Changes

### 1. Dọn dẹp Thư mục Gốc (Root Directory)
Gom nhóm các file test, script bảo trì và tài liệu nằm rải rác ở thư mục gốc vào các thư mục quản lý chuẩn. Tên dự án gốc `Discord_bot` được giữ nguyên.

#### [NEW] `tests/`
- Tích hợp framework **pytest** để chuẩn hóa và dễ dàng bảo trì các bài kiểm thử.
- Đổi tên và cấu trúc lại các script test (ví dụ `run_test_company.py` -> `tests/test_company.py`).

#### [NEW] `scripts/`
- Di chuyển `sync_reports.py`, `check_db_status.py` vào đây.

#### [NEW] `docs/`
- Di chuyển các file `.md` (như `Company_Profiling_Plan.md`, `Implementation_Plan_DB_Cache.md`), `db_summary_view.txt`, và `RAG.html` vào đây.

---

### 2. Tái cấu trúc `src/core/` (Hạ tầng nền tảng)
Lớp Core sẽ chỉ chứa các module không phụ thuộc vào bất kỳ logic nghiệp vụ cụ thể nào, chia thành các package rõ ràng: `db`, `ai`, và `scraper`.

#### [NEW] `src/core/db/`
- **[NEW] `connection.py`**: Được đổi tên và di chuyển từ `src/core/db.py`. Xử lý kết nối `psycopg2` và `asyncpg`.
- **[NEW] `vector.py`**: Được di chuyển từ `src/modules/deep_research/db/pgvector_db.py`. Xử lý toàn bộ logic liên quan đến `pgvector` và RAG search.

#### [NEW] `src/core/ai/`
- **[NEW] `client.py`**: Đổi tên từ `src/core/genai_client.py`. (Singleton quản lý kết nối Gemini).
- **[NEW] `tracker.py`**: Di chuyển từ `src/utils/llm_utils.py`. (Logic đếm token và theo dõi chi phí cuộc gọi LLM).

#### [NEW] `src/core/scraper/`
- **[NEW] `base.py`**: Di chuyển từ `src/utils/base_scanner.py`. (Khung xương cha cho mọi công cụ cào báo cáo).
- **[NEW] `http_client.py`**: Di chuyển từ `src/utils/client.py`.
- **[NEW] `browser.py`**: Gom chung logic từ `src/utils/browser_profiles.py` và `src/utils/user_agent.py`.

---

### 3. Tái cấu trúc `src/utils/` (Tiện ích phụ trợ)
Chỉ chứa các hàm xử lý chuỗi, định dạng ngày tháng không chứa trạng thái (stateless).

#### [MODIFY] `src/utils/`
- **[NEW] `date_parser.py`**: Di chuyển từ `src/modules/deep_research/db/date_utils.py` (Vì xử lý ngày tháng là tác vụ chung, không nên gắn chặt vào RAG DB).
- **[NEW] `ticker.py`**: Đổi tên từ `src/utils/ticker_utils.py` cho chuẩn quy tắc đặt tên.
- **[NEW] `text.py`**: Đổi tên từ `src/utils/tool.py` (vì chứa các hàm xử lý string như `clean_title`).

---

### 4. Tái cấu trúc `src/modules/` (Nghiệp vụ)
Lớp Modules lúc này sẽ rất "sạch sẽ", chỉ chứa luồng chạy chính xác của nghiệp vụ.

#### [MODIFY] `src/modules/deep_research/`
- Xóa bỏ thư mục `db/` bên trong vì tất cả logic database đã chuyển về `src/core/db/`.
- Chỉ giữ lại các Nodes, Tools, State và 2 file Graph chính (`main_graph.py`, `company_graph.py`).

#### [MODIFY] `src/modules/bot_main/`
- File `Bot.py` được chỉnh sửa để trỏ các import về kiến trúc mới (VD: `from src.core.db import AsyncDatabase` $\rightarrow$ `from src.core.db.connection import AsyncDatabase`).

#### [MODIFY] `src/modules/news_summarizer/`
- **[NEW] `ai_helper.py`**: Tạo mới file này và di chuyển hàm `tomtat100` từ `src/core/gg_service.py` sang. Vì tóm tắt nội dung bài báo là logic nghiệp vụ đặc thù của chức năng News Summarizer. Xóa bỏ file `src/core/gg_service.py` sau khi hoàn tất.

---

## Verification Plan

### Automated Tests
- Cài đặt `pytest` và chạy bộ test để đảm bảo các truy xuất database và import không bị gãy:
  ```bash
  pytest tests/
  ```

### Manual Verification
- Chạy thử `python main.py` và đảm bảo Discord Bot vẫn online, không văng lỗi `ModuleNotFoundError`.
- Thử gửi một lệnh `!news` trên kênh Discord test để xác nhận logic truy vấn CSDL cũ hoạt động bình thường.
