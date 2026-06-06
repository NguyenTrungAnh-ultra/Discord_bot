import sys
import os

# Ensure the root folder is in the python path
sys.path.append(os.getcwd())
from src.modules.deep_research.db.pgvector_db import VectorDatabase

def run_migration():
    print("Starting database migration to add `embedded_by` column...")
    
    queries = [
        # 1. Add embedded_by column if not exists
        "ALTER TABLE research_documents ADD COLUMN IF NOT EXISTS embedded_by VARCHAR(100);",
        
        # 2. Backfill existing records with default embedding model
        "UPDATE research_documents SET embedded_by = 'gemini-embedding-2' WHERE embedded_by IS NULL;",
        
        # 3. Create index for the new column to enable fast model filtering
        "CREATE INDEX IF NOT EXISTS idx_research_docs_embedded_by ON research_documents(embedded_by);"
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
