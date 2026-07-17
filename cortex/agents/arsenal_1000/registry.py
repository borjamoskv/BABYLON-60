# C5-REAL CENTURIA REGISTRY COMPRESSED
import sqlite3
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH: Path = Path(__file__).resolve().parent / "primitives.db"

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def get_primitive(primitive_id: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM centuria_primitives WHERE id = ?", (primitive_id,)
        ).fetchone()
        return dict(row) if row else None

def list_primitives_by_domain(domain: str) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM centuria_primitives WHERE domain = ?", (domain,)
        ).fetchall()
        return [dict(r) for r in rows]

def get_all_primitives() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM centuria_primitives").fetchall()
        return [dict(r) for r in rows]

def execute_primitive(primitive_id: str) -> Dict[str, Any]:
    prim = get_primitive(primitive_id)
    if not prim:
        raise ValueError(f"Primitive {primitive_id} not found in Centuria registry.")
    
    timestamp: str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {
        "status": "C5_REAL_EXECUTED",
        "primitive": primitive_id,
        "name": prim["name"],
        "domain": prim["domain"],
        "action": prim["execution"],
        "cortex_taint_hash": prim["cortex_taint_hash"],
        "timestamp": timestamp
    }
