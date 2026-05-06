# Project Overview: Discord Bot Manager

A modular Python-based Discord bot system designed for financial market monitoring, news aggregation, and automated report collection. The project orchestrates multiple specialized modules to provide real-time updates and summarized insights directly to Discord.

## Core Architecture

The system operates as a modular monolith orchestrated by `main.py`. It uses a combination of threading and subprocesses to run various services:

- **Discord Bot (`src/modules/bot_main/Bot.py`)**: The primary interface for users.
  - Commands:
    - `!news [YYYY-MM-DD]`: Fetches news for a specific date or range.
    - `!tomtat`: (Reply to a news embed) Provides an AI-generated summary of the article using Gemini.
    - `!cleanup`: Removes duplicate news/report embeds from the channel.
- **News Summarizer (`src/modules/news_summarizer/`)**:
  - `Firms_news.py`: Periodically fetches news (via `VCI_news`) and sends alerts to a Discord webhook.
  - Uses `vnstock` for real-time stock status (price, volume, change).
- **Report Collector (`src/modules/report_collecter/`)**:
  - `daily_job.py`: Orchestrates daily scraping and delivery.
  - Scanners: ACBS, KBSV, VCBS, SSI, VietCap.
  - `send_wehook.py`: Filters and sends yesterday's reports to Discord webhooks with PDF attachments (where available).
- **Vision Guard (`src/modules/vision_guard/`)**:
  - `VisionGuard.py`: Handles visual monitoring or automated screenshots.

## Shared Services & Utilities

- **AI Service (`src/core/gg_service.py`)**: Integration with Google Generative AI (`gemini-flash-latest`) for article summarization.
- **Logging (`src/core/logger.py`)**: Centralized logging system.
- **Utilities (`src/utils/`)**:
  - `tool.py`: Common helpers for history management, text cleaning, and web scraping.
  - `browser_profiles.py`: Playwright browser configuration.

## Tech Stack

- **Language**: Python 3.10+
- **Frameworks**: `discord.py` (Bot), `playwright` (Scraping), `pandas` (Data processing).
- **AI**: `google-genai` (Gemini API).
- **Data**: `vnstock` for financial data, `requests` for API calls.
- **Orchestration**: `schedule` and `threading` in `main.py`.
- **Deployment**: Docker and Docker Compose.

## Key Directories

- `src/modules/`: Main functional components.
- `src/core/`: Shared core services (AI, Logging).
- `src/utils/`: Generic utility functions.
- `temp/`: Persistent storage for CSVs, JSON trackers, PDF caches, and session cookies. (Note: Historically referred to as `temp/`, check for `temp/` or `Database/reports/` for data).
- `Database/`: Migration plans and structured reports.

## Building and Running

### Prerequisites
- Python 3.10+
- Playwright browsers: `playwright install`
- Valid `.env` file with `DISCORD_TOKEN`, `GEMINI_API_KEY`, and Webhook URLs.

### Local Execution
1. Install dependencies: `pip install -r requirements.txt`
2. Run the orchestrator: `python main.py`

### Docker Execution
```bash
docker-compose up -d --build
```

## Development Conventions

- **Module Resolution**: Always run scripts from the project root. `main.py` and module headers handle `PYTHONPATH` adjustments.
- **Async/Await**: Used extensively in the Discord Bot and AI services.
- **Data Persistence**:
  - News history: `./temp/requested_news.json`
  - Sent reports: `./temp/reports/sent_reports.json`
  - Scraped CSVs: `./temp/reports/{SOURCE}/`
- **Scraping**: Playwright is preferred for sites with heavy JS. Cookie-based authentication (stored in `.pkl` or `.json` in `temp/`) is used for PDF downloads.
- **Environment Variables**: Managed via `.env`. Key variables: `DISCORD_TOKEN`, `GEMINI_API_KEY`, `WEBHOOK_URL_TIN_TUC`, `BAO_CAO_DOANH_NGHIEP`.

## Operational Workflows

- **Daily Reports**: Scanners run every morning at 07:00 (configured in `main.py`).
- **News Alerts**: `Firms_news.py` runs every 1 hour via the scheduler.
- **Bot Heartbeat**: `main.py` monitors and restarts the Bot process if it crashes.
