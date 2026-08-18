# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
BABYLON60 IDE — Read-only database connection pool.
INV_BFT_02 compliant: WAL + busy_timeout=5000 + query_only=ON.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


_BUSY_TIMEOUT_MS = 5000


from babylon60.database.core import connect_sync


def connect_readonly(db_path: str | Path) -> sqlite3.Connection:
    """Read-only connection with INV_BFT_02 pragmas. No mutations allowed."""
    conn = connect_sync(db_path, synchronous="NORMAL")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def get_table_list(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """List all tables in a database with row counts."""
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = []
    for row in cursor.fetchall():
        name = row["name"]
        count_cursor = conn.execute(f'SELECT COUNT(*) as cnt FROM "{name}"')
        count = count_cursor.fetchone()["cnt"]
        tables.append({"name": name, "row_count": count})
    return tables


def get_table_schema(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    """Get column info for a table."""
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


def get_table_rows(
    conn: sqlite3.Connection,
    table: str,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """Paginated table rows."""
    count_cursor = conn.execute(f'SELECT COUNT(*) as cnt FROM "{table}"')
    total = count_cursor.fetchone()["cnt"]
    cursor = conn.execute(f'SELECT * FROM "{table}" LIMIT ? OFFSET ?', (limit, offset))
    rows = [dict(r) for r in cursor.fetchall()]
    columns = [desc[0] for desc in cursor.description] if cursor.description else []
    return {
        "columns": columns,
        "rows": rows,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def execute_readonly_query(conn: sqlite3.Connection, sql: str) -> dict[str, Any]:
    """Execute a read-only SQL query and return results."""
    cursor = conn.execute(sql)
    if cursor.description:
        columns = [desc[0] for desc in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return {"columns": columns, "rows": rows, "row_count": len(rows)}
    return {"columns": [], "rows": [], "row_count": 0}
