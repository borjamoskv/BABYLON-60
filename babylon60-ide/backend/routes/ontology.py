"""
BABYLON60 IDE — Ontology/Database browser API routes.
Auto-discovers .db files and exposes read-only table browsing.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ..services.db_pool import (
    connect_readonly,
    get_table_list,
    get_table_schema,
    get_table_rows,
)

router = APIRouter(prefix="/api/databases", tags=["ontology"])


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def _discover_databases() -> list[dict[str, Any]]:
    """Find all .db files in the project root."""
    root = _get_project_root()
    databases = []
    for db_file in sorted(root.glob("*.db")):
        try:
            size = db_file.stat().st_size
            databases.append({
                "name": db_file.name,
                "path": str(db_file),
                "size_bytes": size,
                "size_human": _human_size(size),
            })
        except OSError:
            continue
    return databases


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size //= 1024
    return f"{size:.1f} TB"


def _resolve_db(name: str) -> Path:
    root = _get_project_root()
    db_path = root / name
    if not db_path.exists():
        raise HTTPException(404, f"Database '{name}' not found")
    if not db_path.suffix == ".db":
        raise HTTPException(400, "Only .db files allowed")
    # Prevent path traversal
    if not db_path.resolve().parent == root.resolve():
        raise HTTPException(403, "Path traversal denied")
    return db_path


@router.get("")
def list_databases() -> list[dict[str, Any]]:
    """List all discovered .db files in the project."""
    return _discover_databases()


@router.get("/{name}/tables")
def list_tables(name: str) -> list[dict[str, Any]]:
    """List tables in a specific database."""
    db_path = _resolve_db(name)
    try:
        conn = connect_readonly(db_path)
        tables = get_table_list(conn)
        conn.close()
        return tables
    except sqlite3.OperationalError as e:
        raise HTTPException(500, f"Database error: {e}") from e


@router.get("/{name}/schema/{table}")
def table_schema(name: str, table: str) -> list[dict[str, Any]]:
    """Get column schema for a table."""
    db_path = _resolve_db(name)
    try:
        conn = connect_readonly(db_path)
        schema = get_table_schema(conn, table)
        conn.close()
        if not schema:
            raise HTTPException(404, f"Table '{table}' not found in '{name}'")
        return schema
    except sqlite3.OperationalError as e:
        raise HTTPException(500, f"Database error: {e}") from e


@router.get("/{name}/tables/{table}")
def browse_table(
    name: str,
    table: str,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Paginated table browser."""
    db_path = _resolve_db(name)
    try:
        conn = connect_readonly(db_path)
        result = get_table_rows(conn, table, limit, offset)
        conn.close()
        return result
    except sqlite3.OperationalError as e:
        raise HTTPException(500, f"Database error: {e}") from e
