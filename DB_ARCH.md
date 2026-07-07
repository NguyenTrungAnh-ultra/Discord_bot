# Database Architecture

The project uses PostgreSQL as the main database management system, combined with the `pgvector` extension to store and search vector embeddings for the AI/RAG system.

Below are the details of the key tables in the system:

## 1. The `research_documents` Table (Vector Database)

This table is the heart of the RAG (Retrieval-Augmented Generation) system, used to store all research documents (analyst reports, company profiles, macro news) and their vectors for similarity search.

**Schema:**
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Auto-incrementing primary key. |
| `url` | `TEXT UNIQUE` | Unique identifier for the document. Contains the real URL (Web PDF) or an internal URL like `internal://...`. Acts as the `UNIQUE` key for the RAG Cache Retrieval Bypass, preventing duplicates, handling upserts, and bypassing expensive scraping/embedding nodes. |
| `title` | `TEXT` | Document title. |
| `content` | `TEXT` | Raw text content of the document for LLM context. |
| `insight` | `JSONB` | Structured data summarized by AI (e.g., financial metrics, business model summaries). |
| `embedding` | `VECTOR(3072)` | Vector embedding of the content/document. Compatible with `gemini-embedding-2` (3072 dimensions). |
| `layer` | `VARCHAR(50)` | Document layer (e.g., `MACRO`, `MICRO`, `COMPANY`). |
| `entities` | `JSONB` | Related entities (e.g., list of stock ticker symbols). |
| `doc_type` | `VARCHAR(50)` | Document classification (e.g., `company_profile`, `financial_report`). |
| `ticker` | `VARCHAR(20)` | Associated ticker symbol (e.g., `VIC`, `HPG`). |
| `publish_date` | `DATE` | Publish date or report period. Used for time-based filtering. |
| `embedded_by` | `VARCHAR(100)` | Model name that generated the embedding (default: `gemini-embedding-2`). |
| `created_at` | `TIMESTAMP` | Timestamp when the record was created in the database. |

**Indexes:**
- `idx_research_docs_ticker` on `(ticker)`
- `idx_research_docs_doc_type` on `(doc_type)`
- `idx_research_docs_publish_date` on `(publish_date)`
- `idx_research_docs_embedded_by` on `(embedded_by)`

---

## 2. The `news` Table (Company News)

This table is used by `Bot.py` and `Firms_news.py` to store financial news scraped from APIs. It helps prevent duplicate messages and allows the Bot to retrieve news data for summarization when requested by users.

**Schema (Based on INSERT statements):**
| Column | Data Type | Description |
| :--- | :--- | :--- |
| `id` | `INT / VARCHAR PRIMARY KEY`| Primary key identifier of the news (derived from the API response ID). Used in `ON CONFLICT (id) DO NOTHING`. |
| `news_title` | `TEXT` | Title of the news article. |
| `ticker` | `VARCHAR` | Ticker symbol affected/mentioned in the news. |
| `news_source_link`| `TEXT` | Original source link of the news. |
| `news_from_name` | `VARCHAR` | News source name (e.g., `VCI`). |
| `update_date` | `TIMESTAMP / DATE` | Timestamp/Date when the news was updated. |
| `sentiment` | `VARCHAR` | Sentiment label evaluated by the system/API (e.g., `Positive`, `Negative`, `Neutral`). |
| `news_short_content`| `TEXT` | Short summary or snippet of the news. |
| `slug` | `VARCHAR` | Identifier string used in the source URL (e.g., `post-detail/{slug}`). |

## Key Mechanisms:
- **Upsert (Update or Insert):** The `research_documents` table uses `ON CONFLICT (url) DO UPDATE` to always keep the latest copy if re-analyzed. The `news` table uses `ON CONFLICT (id) DO NOTHING` to skip if the news already exists.
- **RAG Cache Retrieval Bypass:** The `url` field is strictly defined as `UNIQUE`. Before web scraping or vector embedding generation (which calls the Gemini API), the workflow queries this `url` or metadata (`search_by_metadata`). If found, it loads the `insight` (`JSONB`) directly from DB and bypasses execution, saving tokens, time, and API cost.
