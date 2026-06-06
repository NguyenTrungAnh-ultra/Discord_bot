# Project Architecture

This document details the project architecture, functions of each file and module, and notes where each module is used or called in the workflow.

---

## 1. Configuration (`src/config/`)

- **`const.py`**: Contains system configuration constants.
  - _Usage:_ `HEX_COLOR_...`, `MODEL_MACRO` are called in `Bot.py` and `Firms_news.py`.

---

## 2. Infrastructure Core (`src/core/`)

### 2.1 AI (`src/core/ai/`)

- **`client.py`**: Initializes and manages the singleton `genai.Client` connection to Google Gemini.
  - _Usage:_ Called by `deep_research` (via `tracker.py`) and `news_summarizer` to retrieve the model config.
- **`tracker.py`**: Module for calculating tokens (input/output) by parsing usage_metadata or estimating string length (`estimate_tokens`).
  - _Usage:_ Called by `deep_research` nodes to control LLM limits.

### 2.2 Database (`src/core/db/`)

- **`connection.py`**: Provides `Database` (psycopg2 - synchronous) and `AsyncDatabase` (asyncpg - asynchronous pool) to query PostgreSQL.
  - _Usage:_ `AsyncDatabase` is used by `Bot.py` and `Firms_news.py` to insert and fetch news. `Database` is used by `deep_research`.
- **`vector.py`**: Integrates `pgvector`. Contains embedding insertion/search functions (`search_with_filters`, `search_by_metadata`).
  - _Usage:_ Called by `company_nodes` and `nodes` in `deep_research` to check cache and query RAG. (Redundant function `search_similar` has been cleaned up).

### 2.3 Scraper (`src/core/scraper/`)

- **`base.py`**: Base class `BaseScanner` managing directories, sessions, and saving CSVs.
  - _Usage:_ Scraper files (`ACBS.py`, `KBSV.py`, `VCBS.py`) inherit this class to collect reports.
- **`browser.py`**: Simulates device info (User-Agent, Headers) to prevent blocking.
  - _Usage:_ Called by `text.py` and HTTP clients to bypass anti-bot mechanisms. (Dead code `list_all_profiles` has been cleaned up).
- **`http_client.py`**: Wrapper `send_request()` for calling the `requests` API with error handling and timeouts.
  - _Usage:_ Called by `html_scraper.py` (of Deep Research) to scrape web text content.

### 2.4 Core Utilities

- **`logger.py`**: `get_logger()` function to set up standard logging configuration across the project.

---

## 3. Shared Utilities (`src/utils/`)

- **`date_parser.py` & `ticker.py`**: Support flexible date parsing and ticker symbol manipulation.
  - _Usage:_ Called in Deep Research workflows to normalize tickers and timestamps.
- **`vci_client.py`**: Fetches financial data from the VCI API.
  - _Usage:_ Called by `financial_auditor.py` (in Deep Research) to retrieve financial reports.
- **`text.py`**: Parser to extract HTML/text content.
  - _Usage:_ `get_article()` function is called in the `!tomtat` command of `Bot.py` to extract article content before passing it to AI for summarization. (Typos fixed and cleaned up).

---

## 4. Feature Modules (`src/modules/`)

### 4.1 Discord Bot (`src/modules/bot_main/`)

- **`Bot.py`**: Manages command dispatching (`!news`, `!tomtat`), communicates with the DB, and pushes messages to Webhooks.
  - _Usage:_ Started as an **independent daemon thread** by the `main()` function in `main.py`.

### 4.2 News Summarizer (`src/modules/news_summarizer/`)

- **`Firms_news.py`**: Fetches financial news, filters through the DB to prevent duplicates, and summarizes with Gemini before sending.
  - _Usage:_ Scheduled to run automatically via a bash subprocess (called from `main.py`) **every 1 hour**.

### 4.3 Report Collector (`src/modules/report_collecter/`)

- **`daily_job.py`**: Automated job to trigger scanners sequentially.
  - _Usage:_ Scheduled to run automatically via a bash subprocess (called from `main.py`) at **07:00 daily**.
- **`send_wehook.py`**: Webhook sending script.
  - _Usage:_ Called by `daily_job.py` after scanning finishes.
- **`scanners/ACBS.py`, `KBSV.py`, `VCBS.py`**: Scrape report links from securities firms.
  - _Usage:_ Imported and executed by `daily_job.py`. (Redundant PDF download functions have been completely removed).

### 4.4 Vision Guard (`src/modules/vision_guard/`)

- **`VisionGuard.py`**: Script to capture snapshots of the stock price board (24hmoney.vn) and send them to Discord via Webhook.
  - _Usage:_ Started automatically by `main.py` in a startup thread and scheduled to run daily at **14:50**.

### 4.5 Deep Research (`src/modules/deep_research/`)

This is a massive LangGraph module but contains technical debt:

- **`state.py`, `company_state.py`**: State structure definitions.
  - **[DEAD CODE]**: `current_title`, `current_content`, and `financial_data` variables are not consumed by any node.
- **`main_graph.py`, `company_graph.py`**: Connects nodes (`nodes/`, `company_nodes/`) and tools (`searxng_api.py`, `html_scraper.py`, `pdf_scraper.py`).
  - **[PHANTOM MODULE]**: No function from `main.py` or `Bot.py` imports `create_research_graph` for actual production runs. This large feature is currently only invoked via the test file `test_all_features.py`.
  - **[PHANTOM COMPUTATION]**: The `translator` node generates 10 search queries -> the `searcher` node scrapes 50 URLs. However, the loop is capped at 5 iterations, wasting 45 scraped URLs without processing them.
  - **[FIXED]**: Migrated `company_nodes/cache_checker.py` to direct metadata-based search to fetch the latest records, completely removing the hardcoded URL containing `/2026`.

---

## 5. Root and Test Files (`/`)

- **`main.py`**: Root entry point. Launches the Bot and schedules subprocesses (`job_news`, `job_vision`, `job_daily_report`).
- **`pytest.ini`**: Configuration to auto-discover tests for pytest.
- **`tests/test_all_features.py`**: Contains all E2E and Unit tests running successfully (covering Bot, RAG DB, Utils, LangGraph).
- **[SYSTEM TRASH]**:
  - `tests/request.py`, `tests/sample.txt`, `image.png`, `discord.log`: Junk/draft files that should be deleted.
  - `tests/test_db_schema.py`: Messy output/print code.
  - `tests/test_company.py`, `tests/test_research.py`: Executed manually, not conforming to pytest standards.
  - `tests/caution.txt`, `Implementation Plan.md`: Should be moved to the `docs/` folder.
