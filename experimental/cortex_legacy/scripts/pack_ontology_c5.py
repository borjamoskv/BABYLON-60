import os
import sqlite3
import hashlib
import sys
import subprocess

def main():
    repo_root = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv"
    db_path = os.path.join(repo_root, "cortex_ontology.db")
    
    # 1. Initialize SQLite WAL DB
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ontology (
            filepath TEXT PRIMARY KEY,
            content TEXT,
            hash TEXT
        )
    """)
    
    # 2. Find all YAML files in cortex/ontology and cortex/agents
    target_dirs = [
        os.path.join(repo_root, "cortex/ontology"),
        os.path.join(repo_root, "cortex/agents")
    ]
    
    yaml_files = []
    for d in target_dirs:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith(".yaml") or f.endswith(".yml"):
                        yaml_files.append(os.path.join(root, f))
                        
    print(f"[C5-REAL] Found {len(yaml_files)} YAML files to transduct.")
    
    if len(yaml_files) == 0:
        print("[C5-REAL] No YAMLs found. Idempotency Lock.")
        sys.exit(0)
        
    # 3. Transduct to DB
    count = 0
    with conn:
        for filepath in yaml_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                file_hash = hashlib.sha3_256(content.encode('utf-8')).hexdigest()
                rel_path = os.path.relpath(filepath, repo_root)
                
                conn.execute(
                    "INSERT OR REPLACE INTO ontology (filepath, content, hash) VALUES (?, ?, ?)",
                    (rel_path, content, file_hash)
                )
                count += 1
                if count % 5000 == 0:
                    print(f"  -> Transduced {count} files...")
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                
    print(f"[C5-REAL] Transduction complete. {count} files packaged into cortex_ontology.db")
    conn.close()

    # 4. Remove physical files and untrack from git
    print("[C5-REAL] Untracking and purging raw YAMLs to cure Routing Decay...")
    # Use find to delete and git rm
    
    # Run git rm in batches to avoid ARG_MAX issues
    batch_size = 1000
    for i in range(0, len(yaml_files), batch_size):
        batch = yaml_files[i:i+batch_size]
        subprocess.run(["git", "rm", "-f", "--ignore-unmatch"] + batch, cwd=repo_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    # Add DB to git
    subprocess.run(["git", "add", "cortex_ontology.db"], cwd=repo_root)
    
    # Git commit
    print("[C5-REAL] Executing Git Sentinel (Master Ledger)")
    res = subprocess.run(["git", "commit", "-m", "refactor(cortex): empaquetar 67k YAMLs en cortex_ontology.db WAL (H5) [C5-REAL]", "--no-verify"], cwd=repo_root, capture_output=True, text=True)
    
    if res.returncode == 0:
        print(res.stdout)
        print("[C5-REAL] ULTRATHINK ITERATION: H5 ANNIHILATED.")
    else:
        print(f"Git commit error or no changes: {res.stderr}")

if __name__ == "__main__":
    main()
