# Kế hoạch Chuyển đổi Mã Nguồn sang PostgreSQL

Tài liệu này mô tả chi tiết các bước cần thực hiện để thay thế hoàn toàn hệ thống lưu trữ bằng file `JSON`/`CSV` sang cơ sở dữ liệu `PostgreSQL` (`news_aggregator`, port `5432`).

---

## 🚀 Giai đoạn 1: Chuẩn bị Cốt lõi (Core DB Utilities)

**Mục tiêu:** Tạo một file dùng chung để cung cấp kết nối Database cho tất cả các module.
**Hành động:**
1. Tạo file `src/core/db.py`.
2. Viết class/hàm cung cấp kết nối đồng bộ (`psycopg2`) cho các job ngầm (`Firms_news.py`, `send_wehook.py`, Scanners).
3. Viết class/hàm cung cấp kết nối bất đồng bộ (`asyncpg`) cho Discord Bot (`Bot.py`).
4. Xóa/Đánh dấu Deprecated các hàm đọc ghi file trong `src/utils/tool.py` (`load_history`, `save_history`, `update_history`).

---

## 📰 Giai đoạn 2: Cập nhật Module Tin tức (News)

### 2.1. `src/modules/news_summarizer/Firms_news.py` (Chạy đồng bộ)
*   **Xóa bỏ:** Lấy lịch sử từ `temp/requested_news.json`.
*   **Thêm mới:**
    *   Truy vấn DB để lấy danh sách `id` của các tin đã gửi trong 2 ngày gần nhất: `SELECT id FROM news WHERE update_date >= CURRENT_DATE - INTERVAL '2 days'`.
    *   So sánh tin mới từ API với danh sách `id` lấy từ DB.
    *   Sau khi push Webhook thành công, lập tức `INSERT INTO news` bản ghi đó.

### 2.2. `src/modules/bot_main/Bot.py` (Chạy bất đồng bộ)
*   **Lệnh `!news`:**
    *   Không ghi vào `HISTORY_FILE` nữa.
    *   Sử dụng `asyncpg` để nạp trực tiếp danh sách trả về từ API vào DB (`INSERT ... ON CONFLICT DO NOTHING`).
*   **Lệnh `!tomtat`:**
    *   Không mở file JSON.
    *   Sử dụng lệnh SQL: `SELECT slug, news_source_link FROM news WHERE news_title = $1 LIMIT 1`.

---

## 📊 Giai đoạn 3: Cập nhật Module Báo Cáo (Reports)

### 3.1. `src/modules/report_collecter/send_wehook.py`
*   **Xóa bỏ:** Lịch sử gửi `sent_reports.json`.
*   **Thêm mới:**
    *   **Bước A:** Đọc tất cả các file CSV hiện tại, gán `report_id` (MD5 title), và nạp toàn bộ vào DB (`INSERT INTO report ... ON CONFLICT (report_id) DO NOTHING`).
    *   **Bước B:** Truy vấn các báo cáo chưa gửi: `SELECT * FROM report WHERE is_sent = FALSE LIMIT 30`.
    *   **Bước C:** Gửi Webhook cho danh sách trên.
    *   **Bước D:** Sau khi gửi thành công mỗi báo cáo, đánh dấu: `UPDATE report SET is_sent = TRUE WHERE report_id = %s`.

### 3.2. Cập nhật các Scanners (Tương lai/Tối ưu)
Thay vì các file scanner như `acbs_scraper.py`, `kbsv_scraper.py` xuất ra file `.csv`, ta sẽ cấu hình để chúng chèn (Insert) thẳng vào DB `report` với cờ `is_sent = FALSE`. Khi đó `send_wehook.py` sẽ không cần đọc CSV nữa.

---

## 🧹 Giai đoạn 4: Dọn dẹp & Triển khai

1. Chạy test thử các lệnh `!news`, `!tomtat` trên Discord.
2. Theo dõi log xem Webhook có gửi trùng không.
3. Chạy lệnh xóa toàn bộ thư mục `temp/reports/` (các file `.csv` và `sent_reports.json`).
4. Xóa file `temp/requested_news.json`.
5. Cập nhật lại `requirements.txt` đảm bảo có `asyncpg` và `psycopg2-binary`.

---

> **Bạn có muốn tôi bắt đầu thực hiện Giai đoạn 1 (Tạo file kết nối Core DB) luôn không?**
