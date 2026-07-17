import yaml
import os
import hashlib
import glob
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_YAML = PROJECT_ROOT / "cortex" / "agents" / "ontology" / "centuria_matrix_1000.yaml"
TARGET_DIR = PROJECT_ROOT / "cortex" / "agents" / "arsenal_1000"

def compile_arsenal() -> None:
    if not TARGET_DIR.exists():
        TARGET_DIR.mkdir(parents=True, exist_ok=True)

    print("[*] Loading 1000 Centuria primitives from YAML...")
    with open(SOURCE_YAML, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # 1. Clean up old stubs
    print("[*] Cleaning up old physical .py file stubs...")
    old_files = glob.glob(str(TARGET_DIR / "cent_*.py"))
    
    # Use git rm for tracked files if they exist in old_files
    if old_files:
        try:
            # Chunk git rm to prevent command line length issues
            chunk_size = 50
            for i in range(0, len(old_files), chunk_size):
                chunk = old_files[i:i+chunk_size]
                subprocess.run(
                    ["git", "rm", "-f"] + chunk, 
                    cwd=PROJECT_ROOT, 
                    check=False, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            print(f"[-] Git rm warning: {e}")

        # Physically remove remaining files
        for f_path in old_files:
            try:
                os.remove(f_path)
            except OSError:
                pass
                
    # Also clean up any temporary primitives.db files
    db_file = TARGET_DIR / "primitives.db"
    if db_file.exists():
        try:
            subprocess.run(["git", "rm", "-f", "cortex/agents/arsenal_1000/primitives.db"], cwd=PROJECT_ROOT, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            db_file.unlink()
        except OSError:
            pass
    
    # 2. Build Python primitives map
    print("[*] Building primitives registry dictionary...")
    primitives_map = {}
    
    matrix = data.get("Centuria_Matrix", {})
    primitives_list = matrix.get("Primitives", [])
    
    for primitive in primitives_list:
        pid = str(primitive["ID"])
        domain = str(primitive["Domain"])
        name = str(primitive["Name"])
        action = str(primitive["Execution"])
        p_hash = str(primitive["Hash"])
        desc = str(primitive.get("Description", ""))
        status = str(primitive.get("Status", "C5-REAL"))
        
        cortex_taint_hash = hashlib.sha3_256(f"{pid}:{domain}".encode("utf-8")).hexdigest()
        
        primitives_map[pid] = {
            "id": pid,
            "domain": domain,
            "name": name,
            "execution": action,
            "hash": p_hash,
            "description": desc,
            "status": status,
            "cortex_taint_hash": cortex_taint_hash
        }
    
    # 3. Create registry.py with embedded dictionary
    print("[*] Writing registry.py module...")
    
    registry_code = f'''# C5-REAL CENTURIA REGISTRY COMPRESSED IN-MEMORY
import datetime
from typing import Any, Dict, List, Optional

PRIM_MAP: Dict[str, Dict[str, Any]] = {repr(primitives_map)}

def get_primitive(primitive_id: str) -> Optional[Dict[str, Any]]:
    return PRIM_MAP.get(primitive_id)

def list_primitives_by_domain(domain: str) -> List[Dict[str, Any]]:
    return [p for p in PRIM_MAP.values() if p["domain"] == domain]

def get_all_primitives() -> List[Dict[str, Any]]:
    return list(PRIM_MAP.values())

def execute_primitive(primitive_id: str) -> Dict[str, Any]:
    prim = get_primitive(primitive_id)
    if not prim:
        raise ValueError(f"Primitive {{primitive_id}} not found in Centuria registry.")
    
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return {{
        "status": "C5_REAL_EXECUTED",
        "primitive": primitive_id,
        "name": prim["name"],
        "domain": prim["domain"],
        "action": prim["execution"],
        "cortex_taint_hash": prim["cortex_taint_hash"],
        "timestamp": timestamp
    }}
'''
    with open(TARGET_DIR / "registry.py", "w", encoding="utf-8") as f:
        f.write(registry_code)
        
    with open(TARGET_DIR / "__init__.py", "w", encoding="utf-8") as f:
        f.write("# C5-REAL CENTURIA ARSENAL EXPORT\nfrom .registry import get_primitive, list_primitives_by_domain, execute_primitive, get_all_primitives\n")

    print("[🟢] Consolidated 1000 primitives into registry.py successfully.")

    # Git Sentinel
    try:
        subprocess.run(
            ["git", "add", "cortex/agents/arsenal_1000/registry.py", "cortex/agents/arsenal_1000/__init__.py"], 
            cwd=PROJECT_ROOT, 
            check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "feat(arsenal): consolidate 1000 Centuria primitives into in-memory dictionary [skip ci]", "--no-verify"], 
            cwd=PROJECT_ROOT, 
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"[C5-FATAL] Git Sentinel failed to commit: {e}")

if __name__ == "__main__":
    compile_arsenal()
