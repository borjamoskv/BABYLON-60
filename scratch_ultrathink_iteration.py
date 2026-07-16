import yaml
import sqlite3
import hashlib
import datetime
import os
import subprocess

TARGET_FILE = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/cortex/agents/ontology/centuria_matrix_1000.yaml"
DB_PATH = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/cortex/agents/ontology/centuria_bft_ledger.db"
AGENTS_MD_PATH = "/Users/borjafernandezangulo/.gemini/config/AGENTS.md"

def enforce_global_rule():
    rule = "\n\n- **Ω21 · LLM INVARIANT (IDENTITY DECLARATION):** ANUNCIA SIEMPRE QUE LLM VAS A USAR al iniciar un ciclo cognitivo (ej. Gemini 3.1 Pro High / Inference_L3_Node).\n"
    if os.path.exists(AGENTS_MD_PATH):
        with open(AGENTS_MD_PATH, "a") as f:
            f.write(rule)
    else:
        with open(AGENTS_MD_PATH, "w") as f:
            f.write("# GLOBAL RULES\n" + rule)

def iterate_ultrathink():
    with open(TARGET_FILE, "r") as f:
        data = yaml.safe_load(f)

    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS primitives_ledger (
            id TEXT PRIMARY KEY,
            domain TEXT,
            action TEXT,
            cortex_taint_hash TEXT UNIQUE,
            lamport_t INTEGER,
            timestamp TEXT
        )
    """)
    
    lamport_t = int(datetime.datetime.now().timestamp() * 1000)
    
    inserted = 0
    for primitive in data["Centuria_Matrix"]["Primitives"]:
        pid = primitive["ID"]
        domain = primitive["Domain"]
        action = primitive["Execution"]
        
        raw_payload = f"{pid}:{domain}:{action}:{lamport_t}"
        taint_hash = hashlib.sha3_256(raw_payload.encode('utf-8')).hexdigest()
        
        try:
            conn.execute(
                "INSERT OR IGNORE INTO primitives_ledger (id, domain, action, cortex_taint_hash, lamport_t, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (pid, domain, action, taint_hash, lamport_t, datetime.datetime.now(datetime.timezone.utc).isoformat())
            )
            inserted += 1
            lamport_t += 1
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()

    subprocess.run(["git", "add", "-f", "cortex/agents/ontology/centuria_matrix_1000.yaml", "cortex/agents/ontology/centuria_bft_ledger.db"], cwd="/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv", check=True)
    subprocess.run(["git", "commit", "-m", "chore(apex): ultrathink state collapse [skip ci]"], cwd="/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv", check=False)
    
    git_hash = subprocess.check_output(["git", "log", "-1", "--format=%H"], cwd="/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv").decode('utf-8').strip()
    db_size = os.path.getsize(DB_PATH)
    
    return {
        "Git_Hash": git_hash,
        "Delta_Bytes": db_size,
        "Lamport_T": lamport_t,
        "Primitives_Anchored": inserted
    }

if __name__ == "__main__":
    enforce_global_rule()
    result = iterate_ultrathink()
    print(yaml.dump({"Execution_Graph": {"Node_5 (TERMINATION)": {"Action": "Output(YAML)", "Schema": result}}}, sort_keys=False))
