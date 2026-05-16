# Discord Bot Manager

A modular Python-based Discord bot system designed for financial market monitoring, news aggregation, automated report collection, and deep AI-driven market research. The project orchestrates multiple specialized modules to provide real-time updates and summarized insights directly to Discord.

## 🌟 Core Modules

### 1. Deep Research Engine (New)
An advanced Retrieval-Augmented Generation (RAG) system for corporate and market analysis:
- Built a **LangGraph-based RAG pipeline** to analyze financial reports, using structured prompts to improve accuracy and reduce AI hallucinations.
- Optimized LLM API costs and context windows by implementing **node-level token tracking** and tagging document metadata in **PostgreSQL (pgvector)**.
- Automated financial web scraping using **Playwright**, ensuring the AI's analysis is grounded in the most up-to-date market reports.

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

## 🛠 Tech Stack

- **Language**: Python 3.10+
- **AI & Orchestration**: `google-genai` (Gemini API), `LangGraph`
- **Scraping & Data**: `playwright`, `pandas`, `vnstock`
- **Database**: PostgreSQL (`psycopg2-binary`, `asyncpg`, `pgvector` extension)
- **Bot Framework**: `discord.py`

---

## 💾 Database Architecture

The system is powered by a PostgreSQL database (`news_aggregator`), migrating from legacy JSON/CSV storage.
- **Core DB Utilities**: `src/core/db.py` provides synchronous and asynchronous connection helpers.
- **Vector Storage**: Utilizes `pgvector` for storing embeddings and enabling semantic search across financial reports and company profiles.

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
2. Run the orchestrator: 
   ```bash
   python main.py
   ```

## ⚙️ Operational Workflows
- **Daily Reports**: Scanners run every morning at 07:00 (configured in `main.py`).
- **News Alerts**: Runs every 1 hour via the scheduler.
- **Bot Heartbeat**: `main.py` monitors and restarts the Bot process if it crashes.
