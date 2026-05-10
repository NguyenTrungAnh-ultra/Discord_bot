from src.core.db import Database
try:
    res = Database.execute_query("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'research_documents'", fetch=True)
    if not res:
        print("Table 'research_documents' not found.")
    for row in res:
        print(f"{row['column_name']}: {row['data_type']}")
except Exception as e:
    print(f"Error: {e}")
