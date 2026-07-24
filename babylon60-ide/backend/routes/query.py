"""
BABYLON60 IDE — Read-only SQL query executor.
Enforces PRAGMA query_only=ON to prevent any mutations via the IDE.
"""

from __future__ import annotations

import contextlib
import re
import sqlite3
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.db_pool import connect_readonly, execute_readonly_query

router = APIRouter(prefix="/api/query", tags=["query"])

# Tope de filas por consulta: acota RAM y payload por el puente.
_MAX_ROWS = 1000


class QueryRequest(BaseModel):
    database: str = Field(..., description="Database filename (e.g. master_ledger.db)")
    sql: str = Field(..., description="SQL query to execute (read-only)")


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


@router.post("")
def run_query(req: QueryRequest) -> dict[str, Any]:
    """Execute a read-only SQL query against any discovered database."""
    root = _get_project_root().resolve()
    db_name = Path(req.database).name
    db_path = (root / db_name).resolve()

    if db_path.parent != root:
        raise HTTPException(403, "Path traversal denied")
    if db_path.suffix != ".db":
        raise HTTPException(400, "Only .db files allowed")
    if not db_path.exists():
        raise HTTPException(404, f"Database '{req.database}' not found")

    # Lista BLANCA (más fuerte que la negra anterior): tras retirar
    # comentarios de línea/bloque, la sentencia debe empezar por
    # SELECT / WITH / EXPLAIN. El candado real sigue siendo
    # PRAGMA query_only=ON a nivel de motor; esto es defensa en profundidad
    # y un mensaje claro en vez de un error críptico del motor.
    stripped = re.sub(r"/\*.*?\*/", " ", req.sql, flags=re.DOTALL)
    stripped = re.sub(r"--[^\n]*", " ", stripped).strip()
    first_word = (stripped.split(None, 1)[0].upper() if stripped else "")
    if first_word not in ("SELECT", "WITH", "EXPLAIN"):
        raise HTTPException(
            403,
            f"Solo lectura: la consola acepta SELECT/WITH/EXPLAIN (recibido: '{first_word or '∅'}').",
        )

    try:
        # closing → la conexión se cierra aunque la query lance (antes solo
        # se cerraba en éxito: fuga en cada error SQL). sqlite3.Error cubre
        # OperationalError/DatabaseError/ProgrammingError. El texto SÍ se
        # muestra: es una consola SQL, el error es la señal útil.
        with contextlib.closing(connect_readonly(db_path)) as conn:
            t0 = time.monotonic()
            result = execute_readonly_query(conn, req.sql, max_rows=_MAX_ROWS)
            elapsed_ms = (time.monotonic() - t0) * 1000
        result["elapsed_ms"] = round(elapsed_ms, 2)
        result["database"] = req.database
        return result
    except sqlite3.Error as e:
        raise HTTPException(400, f"SQL error: {e}") from e
