-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create research_documents table
CREATE TABLE IF NOT EXISTS research_documents (
    id SERIAL PRIMARY KEY,
    url TEXT UNIQUE,
    title TEXT,
    content TEXT,
    insight JSONB,
    embedding VECTOR(3072), -- Increased to 3072 for gemini-embedding-2
    layer VARCHAR(50),
    entities JSONB,
    doc_type VARCHAR(50),
    ticker VARCHAR(20),
    publish_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Metadata Filtering
CREATE INDEX IF NOT EXISTS idx_research_docs_ticker ON research_documents(ticker);
CREATE INDEX IF NOT EXISTS idx_research_docs_doc_type ON research_documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_research_docs_publish_date ON research_documents(publish_date);

