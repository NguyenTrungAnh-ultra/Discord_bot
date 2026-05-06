from src.core.db import Database
print(Database.execute_query("SELECT id, COUNT(*) FROM news GROUP BY id HAVING COUNT(*) > 1", fetch=True))
