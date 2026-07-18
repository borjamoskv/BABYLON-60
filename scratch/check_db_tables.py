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
    db1 = os.path.join(root, "cortex.db")
    db2 = os.path.join(root, ".cortex/cortex.db")
    
    s1 = check_db(db1)
    s2 = check_db(db2)
    
    print("cortex.db (root):")
    if s1:
        for t, cols in s1.items():
            print(f"  Table: {t}")
            for col in cols:
                print(f"    {col[1]} ({col[2]})")
    else:
        print("  (Empty or error)")
        
    print("\n.cortex/cortex.db:")
    if s2:
        for t, cols in s2.items():
            print(f"  Table: {t}")
            for col in cols:
                print(f"    {col[1]} ({col[2]})")
    else:
        print("  (Empty or error)")

if __name__ == "__main__":
    main()
