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
  - `send_wehook.py`: Filters and sends yesterday's reports to Discord webhooks with PDF attachments.
- **Vision Guard (`src/modules/vision_guard/`)**:
  - `VisionGuard.py`: Handles visual monitoring or automated screenshots.

## Database Migration (PostgreSQL)

The project is currently migrating from file-based storage (JSON/CSV) to a PostgreSQL database (`news_aggregator`).

- **Core DB Utilities**: `src/core/db.py` provides synchronous (`psycopg2`) and asynchronous (`asyncpg`) connection helpers.
- **Migration Plan**: See `Implementation_Plan.md` for detailed steps.

## Shared Services & Utilities

- **AI Service (`src/core/gg_service.py`)**: Integration with Google Generative AI (`gemini-flash-latest`) for article summarization.
- **Logging (`src/core/logger.py`)**: Centralized logging system.
- **Utilities (`src/utils/`)**:
  - `tool.py`: Common helpers (Note: History functions are DEPRECATED in favor of DB).
  - `browser_profiles.py`: Playwright browser configuration.

## Tech Stack

- **Language**: Python 3.10+
- **Frameworks**: `discord.py` (Bot), `playwright` (Scraping), `pandas` (Data processing).
- **Database**: PostgreSQL (`psycopg2-binary`, `asyncpg`).
- **AI**: `google-genai` (Gemini API). (call model = "gemini-3.1-flash-lite" for testing)
- **Data**: `vnstock` for financial data, `requests` for API calls.
- **Orchestration**: `schedule` and `threading` in `main.py`.

## Building and Running

### Prerequisites

- Python 3.10+
- Playwright browsers: `playwright install`
- PostgreSQL server (configured in `.env`).
- Valid `.env` file with `DISCORD_TOKEN`, `GEMINI_API_KEY`, DB credentials, and Webhook URLs.

### Local Execution

1. Install dependencies: `pip install -r requirements.txt`
2. Run the orchestrator: `python main.py`

## Development Conventions

- **Module Resolution**: Always run scripts from the project root. `main.py` and module headers handle `PYTHONPATH` adjustments.
- **Database Access**: Use `src/core/db.py` for all DB operations. Prefer `AsyncDatabase` for the Discord Bot and `Database` for background jobs.
- **Environment Variables**: Managed via `.env`.

## Operational Workflows

- **Daily Reports**: Scanners run every morning at 07:00 (configured in `main.py`).
- **News Alerts**: `Firms_news.py` runs every 1 hour via the scheduler.
- **Bot Heartbeat**: `main.py` monitors and restarts the Bot process if it crashes.
