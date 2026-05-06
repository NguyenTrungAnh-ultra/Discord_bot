from src.core.db import Database
print("News Duplicates:", Database.execute_query("SELECT id, COUNT(*) FROM news GROUP BY id HAVING COUNT(*) > 1", fetch=True))
print("Report Duplicates:", Database.execute_query("SELECT report_id, COUNT(*) FROM report GROUP BY report_id HAVING COUNT(*) > 1", fetch=True))
print("Total News:", Database.execute_query("SELECT COUNT(*) FROM news", fetch=True)[0]['count'])
print("Total Reports:", Database.execute_query("SELECT COUNT(*) FROM report", fetch=True)[0]['count'])
