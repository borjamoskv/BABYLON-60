# C5-REAL EXERGY CERTIFIED
"""
BABYLON60 IDE — Ontology/Database browser API routes.
Auto-discovers .db files and exposes read-only table browsing.
"""

from __future__ import annotations

import contextlib
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
            databases.append(
                {
                    "name": db_file.name,
                    "path": str(db_file),
                    "size_bytes": size,
                    "size_human": _human_size(size),
                }
            )
        except OSError:
            continue
    return databases


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size //= 1024
    return f"{size:.1f} TB"


import re


def _resolve_db(name: str) -> Path:
    root = _get_project_root().resolve()
    filename = Path(name).name
    if not re.match(r"^[a-zA-Z0-9_\-]+\.db$", filename):
        raise HTTPException(400, "Invalid database filename format. Must be an alphanumeric .db file.")
    db_path = (root / filename).resolve()
    if db_path.parent != root:
        raise HTTPException(403, "Path traversal denied")
    if not db_path.exists():
        raise HTTPException(404, f"Database '{filename}' not found")
    return db_path


@router.get("")
def list_databases() -> list[dict[str, Any]]:
    """List all discovered .db files in the project."""
    return _discover_databases()


# Stable, non-leaking message: never echo raw sqlite text (could leak paths).
_DB_ERR = "No se pudo leer la base (fichero corrupto o no es SQLite)"


@router.get("/{name}/tables")
def list_tables(name: str) -> list[dict[str, Any]]:
    """List tables in a specific database."""
    db_path = _resolve_db(name)
    try:
        # contextlib.closing → conn.close() ocurre también si execute lanza
        # (antes solo se cerraba en la ruta feliz: fuga de conexión).
        with contextlib.closing(connect_readonly(db_path)) as conn:
            return get_table_list(conn)
    except sqlite3.DatabaseError as e:
        raise HTTPException(500, _DB_ERR) from e


@router.get("/{name}/schema/{table}")
def table_schema(name: str, table: str) -> list[dict[str, Any]]:
    """Get column schema for a table."""
    db_path = _resolve_db(name)
    try:
        with contextlib.closing(connect_readonly(db_path)) as conn:
            schema = get_table_schema(conn, table)
    except sqlite3.DatabaseError as e:
        raise HTTPException(500, _DB_ERR) from e
    if not schema:
        raise HTTPException(404, f"Table '{table}' not found in '{name}'")
    return schema


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
        with contextlib.closing(connect_readonly(db_path)) as conn:
            # Validar la tabla contra el catálogo real → 404 claro en vez de
            # un 500 con "no such table" y texto crudo filtrado.
            valid = {t["name"] for t in get_table_list(conn)}
            if table not in valid:
                raise HTTPException(404, f"Table '{table}' not found in '{name}'")
            return get_table_rows(conn, table, limit, offset)
    except sqlite3.DatabaseError as e:
        raise HTTPException(500, _DB_ERR) from e
