from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

_BUSY_TIMEOUT_MS = 5000


def connect_readonly(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA query_only=ON")
    return conn


def get_table_list(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = []
    for row in cursor.fetchall():
        name = row["name"]
        count_cursor = conn.execute(f'SELECT COUNT(*) as cnt FROM "{name}"')
        count = count_cursor.fetchone()["cnt"]
        tables.append({"name": name, "row_count": count})
    return tables


def get_table_schema(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    cursor = conn.execute(f'PRAGMA table_info("{table}")')
    columns = []
    for row in cursor.fetchall():
        columns.append(
            {
                "cid": row["cid"],
                "name": row["name"],
                "type": row["type"],
                "notnull": bool(row["notnull"]),
                "default": row["dflt_value"],
                "pk": bool(row["pk"]),
            }
        )
    return columns


def get_table_rows(conn: sqlite3.Connection, table: str, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    count_cursor = conn.execute(f'SELECT COUNT(*) as cnt FROM "{table}"')
    total = count_cursor.fetchone()["cnt"]
    cursor = conn.execute(f'SELECT * FROM "{table}" LIMIT ? OFFSET ?', (limit, offset))
    rows = [dict(r) for r in cursor.fetchall()]
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    return {"columns": columns, "rows": rows, "total": total, "limit": limit, "offset": offset}


def execute_readonly_query(conn: sqlite3.Connection, sql: str, max_rows: int = 1000) -> dict[str, Any]:
    cursor = conn.execute(sql)
    if cursor.description:
        columns = [desc[0] for desc in cursor.description]
        raw = cursor.fetchmany(max_rows + 1)
        truncated = len(raw) > max_rows
        rows = [dict(zip(columns, row, strict=False)) for row in raw[:max_rows]]
        return {"columns": columns, "rows": rows, "row_count": len(rows), "truncated": truncated}
    return {"columns": [], "rows": [], "row_count": 0, "truncated": False}
