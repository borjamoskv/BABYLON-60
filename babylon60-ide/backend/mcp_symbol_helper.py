import json
import os
import sqlite3
import sys
from typing import Any


def get_db_path() -> str:
    project_root = os.getenv("PORTAL_PROJECT_ROOT", os.getcwd())
    return os.path.join(project_root, "portal_reveng_ledger.db")


def query_ledger(query_type: str, param: str) -> list[dict[str, Any]] | dict[str, Any]:
    db_path = get_db_path()
    if not os.path.exists(db_path):
        return {"error": f"Ledger db not found at {db_path}"}
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA busy_timeout=5000;")
        results: list[dict[str, Any]] | dict[str, Any]
        if query_type == "search":
            cursor.execute(
                "\n                SELECT class_name, module, superclass, ivars_count \n                FROM symbol_index \n                WHERE class_name LIKE ? OR module LIKE ?\n                LIMIT 15;\n            ",
                (f"%{param}%", f"%{param}%"),
            )
            results = [{"class": r[0], "module": r[1], "superclass": r[2], "ivars": r[3]} for r in cursor.fetchall()]
        elif query_type == "get_details":
            cursor.execute(
                "\n                SELECT class_name, module, raw_definition \n                FROM symbol_index \n                WHERE class_name = ?;\n            ",
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
    except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:
        return {"error": str(e)}


def main() -> None:
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: mcp_symbol_helper.py [search|get_details] [param]"}))
        sys.exit(1)
    command = sys.argv[1]
    argument = sys.argv[2]
    output = query_ledger(command, argument)
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
