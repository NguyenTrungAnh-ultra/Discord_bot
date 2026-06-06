import sys
import os

# Đảm bảo nhận diện được thư mục src
sys.path.append(os.getcwd())
from src.modules.deep_research.db.pgvector_db import VectorDatabase

def migrate_db():
    print("Bắt đầu migrate database...")
    queries = [
        "ALTER TABLE research_documents ADD COLUMN IF NOT EXISTS layer VARCHAR(50);",
        "ALTER TABLE research_documents ADD COLUMN IF NOT EXISTS entities JSONB;"
    ]
    
    try:
        for query in queries:
            VectorDatabase.execute_query(query)
            print(f"Executed: {query}")
        print("Migrate database thành công! Đã thêm cột `layer` và `entities`.")
    except Exception as e:
        print(f"Lỗi khi migrate: {e}")

if __name__ == "__main__":
    migrate_db()
