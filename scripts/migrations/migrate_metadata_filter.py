import sys
import os

# Ensure the root folder is in the python path
sys.path.append(os.getcwd())
from src.modules.deep_research.db.pgvector_db import VectorDatabase

def run_migration():
    print("Starting database migration for Metadata Filtering...")
    
    queries = [
        # 1. Add new columns if not exist
        "ALTER TABLE research_documents ADD COLUMN IF NOT EXISTS doc_type VARCHAR(50);",
        "ALTER TABLE research_documents ADD COLUMN IF NOT EXISTS ticker VARCHAR(20);",
        "ALTER TABLE research_documents ADD COLUMN IF NOT EXISTS publish_date DATE;",
        
        # 2. Backfill old data: Update publish_date with created_at::date if publish_date is NULL
        "UPDATE research_documents SET publish_date = created_at::date WHERE publish_date IS NULL;",
        
        # 3. Create indexes for faster queries and filters
        "CREATE INDEX IF NOT EXISTS idx_research_docs_ticker ON research_documents(ticker);",
        "CREATE INDEX IF NOT EXISTS idx_research_docs_doc_type ON research_documents(doc_type);",
        "CREATE INDEX IF NOT EXISTS idx_research_docs_publish_date ON research_documents(publish_date);"
    ]
    
    try:
        for q in queries:
            print(f"Executing: {q}")
            VectorDatabase.execute_query(q)
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error occurred during migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
