# Bản Thiết kế Chi tiết: Hệ thống Phân tích Doanh nghiệp (Company Profiling Engine)

Bản kế hoạch này mô tả kiến trúc kỹ thuật cấp thấp (Low-level design) cho nhánh Phân tích Vi mô. Mục tiêu là xây dựng một hệ thống Multi-Agent chạy hoàn toàn độc lập, tái sử dụng các thư viện Data (VCI API) đã có, và áp dụng chặt chẽ triết lý "Filter - Lọc tinh hoa".

---

## 1. Tổ chức Mã nguồn (Code Structure)
Toàn bộ mã nguồn mới sẽ nằm trong thư mục `src/modules/deep_research/company_nodes/`. Đảm bảo tính "cô lập" tuyệt đối khỏi hệ thống bot Discord chính.

```text
src/modules/deep_research/
├── company_graph.py              # File chính định nghĩa luồng LangGraph
├── company_state.py              # Định nghĩa State dùng chung cho Graph
└── company_nodes/
    ├── profile_builder.py        # Node 1: Đọc text -> Lấy Mô hình KD & Hào quang
    ├── financial_auditor.py      # Node 2: Kéo VCI API -> Đánh giá Tài chính
    ├── company_storer.py         # Node 3: Lưu trữ dữ liệu vào PostgreSQL
    └── report_synthesizer.py     # Node 4: Tổng hợp Báo cáo Đầu tư
```

---

## 2. Quản lý Trạng thái (GraphState)
Tạo file `company_state.py` để định nghĩa cấu trúc dữ liệu truyền qua lại giữa các Node. Khác với Macro RAG, Company RAG cần State đặc thù cho chứng khoán:

```python
from typing import TypedDict, List, Dict, Any

class CompanyState(TypedDict):
    ticker: str                        # Mã chứng khoán (VD: "TCB", "FPT")
    urls: List[str]                    # Các URL báo cáo thường niên/bản cáo bạch
    business_profile: Dict[str, Any]   # Data từ Node 1 (Mô hình KD, Lợi thế)
    financial_data: Dict[str, Any]     # Raw DataFrame từ Node 2 (VCI API)
    financial_insight: Dict[str, Any]  # Phân tích của AI về tài chính (Node 2)
    final_memo: str                    # Báo cáo đầu tư cuối cùng (Node 4)
```

---

## 3. Thiết kế Chi tiết Từng Node (Node Implementations)

### Node 1: `profile_builder.py` (Mô hình Kinh doanh & Lợi thế)
*   **Mục đích:** Xử lý dữ liệu "TĨNH" (Textual Data). Xác định DNA của doanh nghiệp.
*   **Nguồn dữ liệu:** Cào file PDF/HTML từ các nguồn chính thống (Bản cáo bạch, Website doanh nghiệp).
*   **Prompt Logic:** Ép AI xuất JSON.
    ```json
    {
      "chain_of_thought": "...",
      "business_model": {
         "what_they_sell": "...",
         "target_customers": "...",
         "revenue_streams": "..."
      },
      "economic_moat": {
         "moat_type": "Network Effect / High Switching Cost / ...",
         "strength": "High/Medium/Low",
         "evidence": "..."
      }
    }
    ```

### Node 2: `financial_auditor.py` (Kiểm toán Tài chính & Lãnh đạo)
*   **Mục đích:** Xử lý dữ liệu "ĐỘNG" (Quantitative Data). Đánh giá sức khỏe hiện tại.
*   **Tích hợp VCI API:** Import trực tiếp hàm `financial_statement()` từ `No_need/BCTC/explorer/vci/financial1.py`.
*   **Luồng hoạt động:**
    1. Gọi API VCI lấy `BALANCE_SHEET`, `INCOME_STATEMENT`, `CASH_FLOW` theo Quý/Năm.
    2. Format DataFrame thành Markdown/Text String.
    3. Nạp String này vào Prompt cho Gemma 4 31B.
*   **Prompt Logic:**
    > *"Dưới đây là BCTC 4 quý gần nhất của {ticker}. Hãy suy luận (Chain of Thought) về: 1) Biên lợi nhuận gộp có bị thu hẹp không? 2) Dòng tiền hoạt động kinh doanh (CFO) so với Lợi nhuận ròng. 3) Cơ cấu nợ. Trả về JSON."*

### Node 3: `company_storer.py` (Lưu trữ Phân tầng)
*   **Mục đích:** Bơm dữ liệu vào Database Chung (đã upgrade ở Bước 1).
*   **Logic:**
    *   Lưu Profile (Tĩnh): `layer="MICRO"`, `entities={"tickers": ["TCB"], "type": "core_profile"}`
    *   Lưu Tài chính (Động): `layer="MICRO"`, `entities={"tickers": ["TCB"], "type": "financial_Q3_2026"}`
    *   Điều này cho phép hệ thống Vĩ mô sau này query chéo dễ dàng.

### Node 4: `report_synthesizer.py` (Màng lọc Tinh hoa)
*   **Mục đích:** Tổng hợp `business_profile` và `financial_insight` thành một Investment Memo.
*   **Triết lý "The Filter":**
    *   **Context:** Truyền Toàn bộ dữ liệu thô vào Prompt.
    *   **Bắt buộc:** Yêu cầu mô hình tạo thẻ `<think>` để tranh luận nội bộ về dữ kiện.
    *   **Thành phẩm:** Báo cáo đầu ra (ngoài thẻ `<think>`) CHỈ chứa Luận điểm Đầu tư (Thesis), Rủi ro cốt lõi (Risks), và Định giá sơ bộ (Valuation hints). TUYỆT ĐỐI KHÔNG copy-paste lại BCTC vào báo cáo.

---

## 4. Cơ chế Kích hoạt (Trigger Mechanism)
Vì tính chất dữ liệu khác nhau, hệ thống Company Profiling không chạy quét liên tục như SearxNG:
1. **On-Demand (Gọi bằng lệnh):** Người dùng gõ lệnh `!analyze TCB`.
2. **Batch Job (Định kỳ mùa BCTC):** Cứ đến tháng 1, 4, 7, 10, tự động chạy một script lặp qua danh sách 50 mã VN30+ để cập nhật `financial_data` mới nhất vào DB `pgvector`.
