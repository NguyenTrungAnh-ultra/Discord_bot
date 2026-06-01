# Discord Bot Manager

A modular Python-based Discord bot system designed for financial market monitoring, news aggregation, automated report collection, and deep AI-driven market research. The project orchestrates multiple specialized modules to provide real-time updates and summarized insights directly to Discord.

---

## 🌟 Core Modules

### 1. Deep Research & Metadata Filtering RAG Engine (v2.0)

An advanced, cost-optimized Retrieval-Augmented Generation (RAG) system for corporate and market analysis built on **LangGraph**:

- **Hybrid RAG & Metadata Filtering (New)**: Adds PostgreSQL (`pgvector`) metadata columns (`ticker`, `doc_type`, `publish_date`) and fast indexes. Supports vector similarity search restricted by tickers, document types, or specific date ranges (`search_with_filters`).
- **Chronological Date Extraction**: Uses structured Gemini prompts to extract `publish_date` and `report_date` from web sources and PDF annual reports. Normalizes quarter data (e.g. `Q3/2024` $\rightarrow$ `30/09/2024`) and year data (e.g. `2024` $\rightarrow$ `31/12/2024`) via a robust parser.
- **Memory Retriever Node**: Intercepts the Macro Research Graph right after query translation. Detects stock symbols (e.g. `VIC`, `TCB`), performs filtered vector database queries, and loads historical insights into the state (`db_insights`) for comparative analysis.
- **Optimal Resource Caching (Cache Bypass)**: The Company Graph (`company_graph.py`) first checks the DB (`cache_checker`). If a company profile or financial insight exists, it **bypasses and skips all web searches, PDF scraping, and LLM analysis nodes**, saving up to **95% of execution time and API token costs**.
- **Chained Node-Level Token Tracking**: Estimates and records total input/output tokens and request counts per node.

### 2. Discord Bot (`src/modules/bot_main/`)

The primary interface for users to interact with the system.

- Commands:
  - `!news [YYYY-MM-DD]`: Fetches news for a specific date or range.
  - `!tomtat`: (Reply to a news embed) Provides an AI-generated summary of the article using Gemini.
  - `!cleanup`: Removes duplicate news/report embeds from the channel.

### 3. News Summarizer (`src/modules/news_summarizer/`)

- Periodically fetches news (via `VCI_news`) and sends alerts to a Discord webhook.
- Uses `vnstock` for real-time stock status (price, volume, change).

### 4. Report Collector (`src/modules/report_collecter/`)

- Orchestrates daily scraping and delivery of financial reports.
- Scanners for multiple sources: ACBS, KBSV, VCBS, SSI, VietCap.
- Filters and sends yesterday's reports to Discord webhooks with PDF attachments.

### 5. Vision Guard (`src/modules/vision_guard/`)

- Handles visual monitoring or automated screenshots of financial charts/dashboards.

---

## 📐 System Architecture & Workflow

Here is the complete E2E system workflow depicting both **Macro & Sector System** and **Company Micro System** interacting with the central **pgvector RAG Database** and utilizing the optimized Cache Bypass.

```mermaid
graph TD
    classDef startEnd fill:#10b981,stroke:#059669,stroke-width:2px,color:#fff;
    classDef nodeClass fill:#1e293b,stroke:#0ea5e9,stroke-width:2px,color:#f1f5f9;
    classDef dbClass fill:#0284c7,stroke:#0369a1,stroke-width:2px,color:#fff;
    classDef decisionClass fill:#d97706,stroke:#b45309,stroke-width:2px,color:#fff;
    classDef skipClass fill:#ef4444,stroke:#dc2626,stroke-width:2px,color:#fff;

    Start(("Bắt đầu Yêu cầu")) --> QueryRouter{"Query Router / Phân loại Đầu vào"}

    %% -----------------------------------------
    %% SUBGRAPH 1: MACRO & SECTOR GRAPH (MAIN GRAPH)
    %% -----------------------------------------
    subgraph MacroSectorSystem ["LUỒNG PHÂN TÍCH VĨ MÔ VÀ NGÀNH - Main Research Graph"]
        QueryRouter -->|Truy vấn Vĩ mô hoặc Ngành| TranslatorNode["1. Translator Node (Phân tích và sinh 6-10 câu tìm kiếm)"]

        TranslatorNode --> MemoryRetrieverNode["2. Memory Retriever Node (Trích xuất Ticker - Lọc DB và nạp db_insights)"]

        MemoryRetrieverNode --> SearcherNode["3. Searcher Node (Tìm kiếm rộng qua SearxNG)"]

        SearcherNode --> DispatcherNode{"4. Dispatcher Node (Vòng lặp URLs)"}

        DispatcherNode -->|Còn URL và dưới giới hạn| ProcessorNode["5. Processor Node (Scrape HTML/PDF và AI trích xuất publish_date)"]

        ProcessorNode --> StorerNode["6. Storer Node (Tạo Vector 3072 và Lưu DB kèm ticker, doc_type, publish_date)"]

        StorerNode --> DispatcherNode

        DispatcherNode -->|Hết URL hoặc Đạt Giới hạn| ReporterNode["7. Reporter Node (AI tổng hợp insights mới và db_insights lịch sử)"]
    end

    %% -----------------------------------------
    %% SUBGRAPH 2: COMPANY MICRO GRAPH (COMPANY GRAPH)
    %% -----------------------------------------
    subgraph CompanySystem ["LUỒNG PHÂN TÍCH DOANH NGHIỆP - Company Graph"]
        QueryRouter -->|Mã cổ phiếu ví dụ VIC| CacheCheckerNode["Node 0: Cache Checker (Tra cứu URL và search_by_metadata lấy bản mới nhất)"]

        CacheCheckerNode --> ProfileCacheCheck{"Đã có Profile?"}

        ProfileCacheCheck -->|Chưa có| ProfileBuilderNode["Node 1: Profile Builder (Tìm Báo cáo thường niên/Cáo bạch và trích xuất report_date)"]
        ProfileCacheCheck -->|Đã có - Bypass| SkipProfile["Bỏ qua Tìm kiếm và Phân tích"]

        ProfileBuilderNode --> FinanceCacheCheck{"Đã có tài chính?"}
        SkipProfile --> FinanceCacheCheck

        FinanceCacheCheck -->|Chưa có| FinancialAuditorNode["Node 2: Financial Auditor (Kéo BCTC từ VCI và AI phân tích sức khỏe)"]
        FinanceCacheCheck -->|Đã có - Bypass| SkipFinance["Bỏ qua gọi API và phân tích tài chính"]

        FinancialAuditorNode --> CompanyStorerNode["Node 3: Company Storer (Tạo Vector 3072 và Lưu profile/BCTC theo Quý)"]
        SkipFinance --> CompanyStorerNode

        CompanyStorerNode --> ReportSynthesizerNode["Node 4: Report Synthesizer (AI liên kết dữ liệu lập Investment Memo)"]
    end

    %% -----------------------------------------
    %% CENTRAL DATABASE
    %% -----------------------------------------
    subgraph DatabaseSystem ["HỆ THỐNG CƠ SỞ DỮ LIỆU RAG - pgvector"]
        DB[(PostgreSQL Database - Bảng research_documents kèm các chỉ mục idx_ticker, idx_doc_type, idx_publish_date)]
    end

    %% DB Connections
    MemoryRetrieverNode -. "Truy vấn tương đồng vector" .-> DB
    StorerNode -->|Lưu tài liệu vĩ mô| DB
    CacheCheckerNode -. "Truy vấn tương đồng metadata" .-> DB
    CompanyStorerNode -->|Lưu hồ sơ và BCTC| DB

    %% Output
    ReporterNode --> FinalMacroReport[/"Báo cáo Vĩ mô và Ngành"/]
    ReportSynthesizerNode --> FinalMicroMemo[/"Investment Memo VIC / TCB"/]

    FinalMacroReport --> End(("Kết thúc"))
    FinalMicroMemo --> End

    class Start,End startEnd;
    class TranslatorNode,MemoryRetrieverNode,SearcherNode,ProcessorNode,StorerNode,ReporterNode nodeClass;
    class CacheCheckerNode,ProfileBuilderNode,FinancialAuditorNode,CompanyStorerNode,ReportSynthesizerNode nodeClass;
    class DB dbClass;
    class QueryRouter,ProfileCacheCheck,FinanceCacheCheck,DispatcherNode decisionClass;
    class SkipProfile,SkipFinance skipClass;
```

---

## 🛠 Tech Stack

- **Language**: Python 3.10+
- **AI & Orchestration**: `google-genai` (Gemini API), `LangGraph`
- **Scraping & Data**: `playwright`, `pandas`, `vnstock`
- **Database**: PostgreSQL (`psycopg2-binary`, `asyncpg`, `pgvector` extension)
- **Bot Framework**: `discord.py`

---

## 💾 Database Architecture & Migrations

The system is powered by a PostgreSQL database (`news_aggregator`) with the `pgvector` extension.

- **Core DB Utilities**: `src/core/db.py` provides synchronous and asynchronous connection helpers.
- **Standard Tables**: `news` and `report` store aggregated market news and scraped financial reports. Detailed schema is available in `Database/Schema.md`.
- **RAG Schema (`src/modules/deep_research/db/schema.sql`)**: Contains the `research_documents` table with advanced columns (`ticker`, `doc_type`, `publish_date`, `layer`, `entities`).
- **Migrations**:
  - `migrate_rag_db.py`: Backfilled standard layers.
  - `migrate_metadata_filter.py`: Configures metadata columns, runs fallback backfills, and sets up high-speed indexes for dynamic filtering.

---

## 🛠 Utilities & Maintenance

- **`sync_reports.py`**: Syncs previously sent report history (using MD5 hashes of report titles) to avoid duplicate Discord notifications.
- **`check_db_status.py`**: Utility script to check for duplicates and total row counts in the `news` and `report` tables.

---

## 🚀 Building and Running

### Prerequisites

- Python 3.10+
- Playwright browsers: Run `playwright install`
- PostgreSQL server (with `pgvector` installed) configured in `.env`.
- Valid `.env` file with `DISCORD_TOKEN`, `GEMINI_API_KEY`, DB credentials, and Webhook URLs.

### Local Execution

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run database migration (if starting fresh):
   ```bash
   python src/modules/deep_research/db/migrate_metadata_filter.py
   ```
3. Run the orchestrator:
   ```bash
   python main.py
   ```

### Running Tests

- **Integration Tests (Metadata RAG)**: Run 3 consecutive test suites to verify embedding insertion, date parsing, vector filters, and metadata check skips:
  ```bash
  python scratch/test_metadata_rag.py
  ```
- **Company Graph Test (Micro Research)**:
  ```bash
  python run_test_company.py
  ```
- **Research Graph Test (Macro Research)**:
  ```bash
  python run_test_research.py
  ```
