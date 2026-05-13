import sys
import os
sys.path.append(os.getcwd())
from src.modules.deep_research.db.pgvector_db import VectorDatabase

def check_research_schema():
    print("Checking research_documents schema...")
    try:
        schema = VectorDatabase.execute_query("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'research_documents'
        """, fetch=True)
        for col in schema:
            print(f"{col['column_name']}: {col['data_type']}")
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == "__main__":
    check_research_schema()
