import sqlite3

conn = sqlite3.connect("agent_memory.db")
cursor = conn.cursor()

# Search for training, train, model, etc.
query = """
SELECT id, issue_id, agent_role, action, result, timestamp 
FROM decisions 
WHERE action LIKE '%model%' OR action LIKE '%train%' OR action LIKE '%entrenado%' OR action LIKE '%lora%' OR action LIKE '%fine-tune%'
   OR result LIKE '%model%' OR result LIKE '%train%' OR result LIKE '%entrenado%' OR result LIKE '%lora%' OR result LIKE '%fine-tune%'
ORDER BY timestamp DESC
LIMIT 50;
"""

cursor.execute(query)
rows = cursor.fetchall()
for r in rows:
    print(f"ID: {r[0]}, Issue: {r[1]}, Role: {r[2]}")
    print(f"Action: {r[3][:200]}")
    print(f"Result: {r[4][:200]}")
    print(f"Timestamp: {r[5]}")
    print("-" * 50)

conn.close()
