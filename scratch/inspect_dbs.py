import sqlite3
import os

dbs = ["agent_memory.db", "cognitive_state.db", "cortex.db", ".cortex/cortex.db", "db/centuria_github.db"]

for db in dbs:
    if os.path.exists(db):
        print(f"=== {db} ===")
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables:", [t[0] for t in tables])
        for table in tables:
            t_name = table[0]
            cursor.execute(f"PRAGMA table_info({t_name});")
            info = cursor.fetchall()
            print(f"  Table {t_name} schema:")
            for col in info:
                print(f"    {col[1]} ({col[2]})")
            # count
            cursor.execute(f"SELECT count(*) FROM {t_name};")
            count = cursor.fetchone()[0]
            print(f"    Rows: {count}")
        conn.close()
    else:
        print(f"=== {db} (not found) ===")
