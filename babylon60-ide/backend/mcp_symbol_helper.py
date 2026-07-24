#!/usr/bin/env python3
import json
import os
import sqlite3
import sys


def get_db_path():
    project_root = os.getenv("PORTAL_PROJECT_ROOT", os.getcwd())
    return os.path.join(project_root, "portal_reveng_ledger.db")


def query_ledger(query_type, param):
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return {"error": f"Ledger db not found at {db_path}"}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA busy_timeout=5000;")

        if query_type == "search":
            cursor.execute(
                """
                SELECT class_name, module, superclass, ivars_count 
                FROM symbol_index 
                WHERE class_name LIKE ? OR module LIKE ?
                LIMIT 15;
            """,
                (f"%{param}%", f"%{param}%"),
            )
            results = [{"class": r[0], "module": r[1], "superclass": r[2], "ivars": r[3]} for r in cursor.fetchall()]

        elif query_type == "get_details":
            cursor.execute(
                """
                SELECT class_name, module, raw_definition 
                FROM symbol_index 
                WHERE class_name = ?;
            """,
                (param,),
            )
            row = cursor.fetchone()
            results = (
                {"class": row[0], "module": row[1], "definition": row[2]} if row else {"error": "Symbol not found"}
            )

        else:
            results = {"error": "Invalid query type"}

        conn.close()
        return results
    except Exception as e:
        return {"error": str(e)}


def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: mcp_symbol_helper.py [search|get_details] [param]"}))
        sys.exit(1)

    command = sys.argv[1]
    argument = sys.argv[2]

    output = query_ledger(command, argument)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
