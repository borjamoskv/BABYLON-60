# C5-REAL EXERGY CERTIFIED
"""
BABYLON60 IDE — Read-only SQL query executor.
Enforces PRAGMA query_only=ON to prevent any mutations via the IDE.
"""

from __future__ import annotations

import contextlib
import sqlite3
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.db_pool import connect_readonly, execute_readonly_query

router = APIRouter(prefix="/api/query", tags=["query"])


class QueryRequest(BaseModel):
    database: str = Field(..., description="Database filename (e.g. master_ledger.db)")
    sql: str = Field(..., description="SQL query to execute (read-only)")


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


import re


@router.post("")
def run_query(req: QueryRequest) -> dict[str, Any]:
    """Execute a read-only SQL query against any discovered database."""
    root = _get_project_root().resolve()
    filename = Path(req.database).name
    if not re.match(r"^[a-zA-Z0-9_\-]+\.db$", filename):
        raise HTTPException(400, "Invalid database filename format. Must be an alphanumeric .db file.")

    db_path = (root / filename).resolve()
    if db_path.parent != root:
        raise HTTPException(403, "Path traversal denied")
    if not db_path.exists():
        raise HTTPException(404, f"Database '{filename}' not found")

    # Block obvious write statements at the string level as defense-in-depth
    sql_upper = req.sql.strip().upper()
    blocked = (
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "CREATE",
        "ATTACH",
        "DETACH",
        "PRAGMA",
        "VACUUM",
        "REINDEX",
    )
    for kw in blocked:
        if sql_upper.startswith(kw):
            raise HTTPException(403, f"Write operation '{kw}' blocked. IDE is read-only.")

    try:
        # closing → la conexión se cierra aunque la query lance (antes solo
        # se cerraba en éxito: fuga en cada error SQL). sqlite3.Error cubre
        # OperationalError/DatabaseError/ProgrammingError. El texto SÍ se
        # muestra: es una consola SQL, el error es la señal útil.
        with contextlib.closing(connect_readonly(db_path)) as conn:
            t0 = time.monotonic()
            result = execute_readonly_query(conn, req.sql)
            elapsed_ms = (time.monotonic() - t0) * 1000
        result["elapsed_ms"] = round(elapsed_ms, 2)
        result["database"] = req.database
        return result
    except sqlite3.Error as e:
        raise HTTPException(400, f"SQL error: {e}") from e
