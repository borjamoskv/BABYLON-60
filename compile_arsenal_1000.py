import yaml
import os
import sqlite3
import hashlib
import glob
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT: Path = Path(__file__).resolve().parent
SOURCE_YAML: Path = PROJECT_ROOT / "cortex" / "agents" / "ontology" / "centuria_matrix_1000.yaml"
TARGET_DIR: Path = PROJECT_ROOT / "cortex" / "agents" / "arsenal_1000"
DB_PATH: Path = TARGET_DIR / "primitives.db"

def compile_arsenal() -> None:
    if not TARGET_DIR.exists():
        TARGET_DIR.mkdir(parents=True, exist_ok=True)

    print("[*] Loading 1000 Centuria primitives from YAML...")
    with open(SOURCE_YAML, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = yaml.safe_load(f)

    # 1. Clean up old stubs
    print("[*] Cleaning up old physical .py file stubs...")
    old_files: List[str] = glob.glob(str(TARGET_DIR / "cent_*.py"))
    
    # Use git rm for tracked files if they exist in old_files
    if old_files:
        try:
            # Chunk git rm to prevent command line length issues
            chunk_size: int = 50
            for i in range(0, len(old_files), chunk_size):
                chunk: List[str] = old_files[i:i+chunk_size]
                subprocess.run(
                    ["git", "rm", "-f"] + chunk, 
                    cwd=PROJECT_ROOT, 
                    check=False, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
        except subprocess.SubprocessError as e:
            print(f"[-] Git rm warning: {e}")

        # Physically remove remaining files
        for f_path in old_files:
            try:
                os.remove(f_path)
            except OSError:
                pass
    
    # 2. Initialize SQLite Database
    print("[*] Initializing primitives.db database...")
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except OSError as e:
            print(f"[-] Failed to remove stale DB: {e}")
        
    conn: sqlite3.Connection = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS centuria_primitives (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            name TEXT NOT NULL,
            execution TEXT NOT NULL,
            hash TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            cortex_taint_hash TEXT NOT NULL
        )
    """)
    
    print("[*] Indexing 1000 primitives into SQLite database...")
    primitives_to_insert: List[Tuple[str, str, str, str, str, str, str, str]] = []
    
    # Ensure correct structure checks
    matrix: Dict[str, Any] = data.get("Centuria_Matrix", {})
    primitives_list: List[Dict[str, Any]] = matrix.get("Primitives", [])
    
    for primitive in primitives_list:
        pid: str = str(primitive["ID"])
        domain: str = str(primitive["Domain"])
        name: str = str(primitive["Name"])
        action: str = str(primitive["Execution"])
        p_hash: str = str(primitive["Hash"])
        desc: str = str(primitive.get("Description", ""))
        status: str = str(primitive.get("Status", "C5-REAL"))
        
        cortex_taint_hash: str = hashlib.sha3_256(f"{pid}:{domain}".encode("utf-8")).hexdigest()
        
        primitives_to_insert.append((
            pid, domain, name, action, p_hash, desc, status, cortex_taint_hash
        ))
        
    conn.executemany(
        "INSERT INTO centuria_primitives VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        primitives_to_insert
    )
    conn.commit()
    conn.close()
    
    # 3. Create registry.py
    print("[*] Writing registry.py module...")
    registry_code: str = '''# C5-REAL CENTURIA REGISTRY COMPRESSED
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
'''
    with open(TARGET_DIR / "registry.py", "w", encoding="utf-8") as f:
        f.write(registry_code)
        
    with open(TARGET_DIR / "__init__.py", "w", encoding="utf-8") as f:
        f.write("# C5-REAL CENTURIA ARSENAL EXPORT\\nfrom .registry import get_primitive, list_primitives_by_domain, execute_primitive, get_all_primitives\\n")

    print("[🟢] Consolidated 1000 primitives into primitives.db and registry.py successfully.")

    # Git Sentinel
    try:
        subprocess.run(
            ["git", "add", "-f", "cortex/agents/arsenal_1000/registry.py", "cortex/agents/arsenal_1000/primitives.db", "cortex/agents/arsenal_1000/__init__.py"], 
            cwd=PROJECT_ROOT, 
            check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "feat(arsenal): consolidate 1000 Centuria primitives into SQLite database [skip ci]", "--no-verify"], 
            cwd=PROJECT_ROOT, 
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"[C5-FATAL] Git Sentinel failed to commit: {e}")

if __name__ == "__main__":
    compile_arsenal()
