import sqlite3
import os

def check_db(db_path):
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        table_schemas = {}
        for t in tables:
            cursor.execute(f"PRAGMA table_info({t});")
            table_schemas[t] = cursor.fetchall()
        conn.close()
        return table_schemas
    except Exception as e:
        return f"Error: {e}"

def main():
    root = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
    dbs = ["cognitive_state.db", "agent_memory.db"]
    
    for db_name in dbs:
        db_path = os.path.join(root, db_name)
        s = check_db(db_path)
        print(f"{db_name}:")
        if s:
            for t, cols in s.items():
                print(f"  Table: {t}")
                for col in cols:
                    print(f"    {col[1]} ({col[2]})")
        else:
            print("  (Empty or error)")
        print()

if __name__ == "__main__":
    main()
