# Deep Research Module Documentation

This document summarizes the development, implementation details, and troubleshooting steps for the **Deep Research** module in the Discord Bot project.

## Overview
The Deep Research module is an autonomous research agent built using **LangGraph** and **Google Gemini**. It performs iterative searches, scrapes web content (HTML and PDF), extracts key insights, stores them in a vector database, and synthesizes a comprehensive final report.

## Core Architecture
The system is designed as a state machine using `langgraph`, allowing for an iterative research loop:

1.  **Translator Node**: Refines the user's research query into optimized search terms, stripping conversational filler.
2.  **Searcher Node**: Queries **SearxNG** (self-hosted) to find relevant URLs.
3.  **Dispatcher Node**: Manages a queue of URLs to be processed.
4.  **Processor Node**: Scrapes content using `trafilatura` (HTML) or `PyMuPDF` (PDF) and extracts structured JSON insights using Gemini.
5.  **Storer Node**: Generates embeddings for the insights using `gemini-embedding-2` and stores them in a **PostgreSQL (pgvector)** database.
6.  **Reporter Node**: Synthesizes all gathered information from the database into a final, detailed markdown report.

## Infrastructure
-   **SearxNG**: A privacy-respecting search engine running via Docker.
    -   Configuration: `searxng/settings.yml` (enables JSON output).
-   **PostgreSQL + pgvector**: Used for high-dimensional vector search.
    -   Table: `research_documents`.
    -   Dimension: 3072 (optimized for `text-embedding-004`/`gemini-embedding-2`).

## Key Challenges & Resolutions

### 1. Vector Dimension Mismatch
-   **Issue**: Initial schema used 768 or 1536 dimensions, but the latest Gemini embedding models (`gemini-embedding-2`) output 3072 dimensions.
-   **Resolution**: Updated `src/modules/deep_research/db/schema.sql` and `pgvector_db.py` to support 3072 dimensions. Re-indexed the database.

### 2. Gemini API Errors (`404 NOT_FOUND` & `PERMISSION_DENIED`)
-   **Issue**: Some model strings (e.g., `gemini-2.0-flash-thinking`) were unavailable or required specific API permissions/keys.
-   **Resolution**: 
    -   Rotated API keys to ensure valid quota.
    -   Standardized model usage to `gemini-flash-latest` for nodes and `gemini-2.0-flash` (or fallback) for the final report.
    -   Implemented robust error handling for API failures.

### 3. `psycopg2` / `pgvector` Integration
-   **Issue**: `register_vector()` from the `pgvector` library would crash if the `vector` extension wasn't explicitly enabled or if there were version mismatches in the DB.
-   **Resolution**: Added a `HAS_PGVECTOR` flag and wrapped the registration in a `try-except` block in `pgvector_db.py`. This allows the system to continue (with degraded search) even if the extension is momentarily unavailable.

### 4. SearxNG Configuration
-   **Issue**: Default SearxNG installations do not return JSON, causing the `Searcher` node to fail.
-   **Resolution**: Created a custom `searxng/settings.yml` and mounted it into the Docker container to force-enable the JSON format.

### 5. Python 3.14 / Pydantic Compatibility
-   **Issue**: Running on Python 3.14 caused issues with older versions of Pydantic and LangGraph.
-   **Resolution**: Updated `requirements.txt` to use compatible versions and patched `main_graph.py` to ensure type safety.

## How to Run
1.  **Start Infrastructure**:
    ```bash
    docker-compose up -d searxng
    ```
2.  **Verify DB**: Run `test_db_schema.py` to ensure `pgvector` is ready.
3.  **Execute Research**:
    ```python
    python run_test_research.py
    ```

## Future Work
-   **Discord Integration**: Add a `!deep_research` command to the bot.
-   **Memory Management**: Implement automatic cleanup of old research data in the vector DB.
-   **Cost Tracking**: Log token usage for Gemini API calls per research session.
