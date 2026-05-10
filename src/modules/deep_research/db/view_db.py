import sys
import os
import json

# Đảm bảo nhận diện được thư mục src
sys.path.append(os.getcwd())
from src.modules.deep_research.db.pgvector_db import VectorDatabase

def export_db():
    query = "SELECT url, title, content FROM research_documents ORDER BY id DESC LIMIT 10;"
    try:
        results = VectorDatabase.execute_query(query, fetch=True)
        if not results:
            print("Database dang trong.")
            return

        output_file = "db_summary_view.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            for i, row in enumerate(results):
                f.write(f"--- KET QUA {i+1} ---\n")
                f.write(f"URL: {row['url']}\n")
                f.write(f"TIEU DE: {row['title']}\n")
                f.write(f"TOM TAT: {row['content']}\n")
                f.write("-" * 50 + "\n\n")
        
        print(f"Da xuat du lieu ra file '{output_file}'. Ban hay mo file do de xem nhe!")
    except Exception as e:
        print(f"Loi: {e}")

if __name__ == "__main__":
    export_db()
