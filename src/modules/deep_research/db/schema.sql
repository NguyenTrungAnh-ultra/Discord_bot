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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Note: HNSW index is disabled for dimensions > 2000 in some PG versions/configs.
-- For a small research dataset, sequential scan or a different index type is sufficient.
-- CREATE INDEX ON research_documents USING hnsw (embedding vector_cosine_ops);
