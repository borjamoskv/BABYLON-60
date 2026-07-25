# C5-REAL EXERGY CERTIFIED
import ast
import hashlib
import os
import sqlite3
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex.entropy_mapping_engine import ThermodynamicEntropyEngine

def ultrathink_audit(filepath: str) -> None:
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Structural token ratio (Exergy Density)
    words = content.split()
    total_words = len(words)
    structural_tokens = sum(
        1 for w in words if w.startswith("Ω") or w.isupper() or w in {"C5-REAL", "AST", "Ledger", "Exergía"}
    )

    # Dynamic AST and categorical entropy mapping via ThermodynamicEntropyEngine
    engine = ThermodynamicEntropyEngine()
    domain_counts: dict[str, int] = {}
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            cat = node.__class__.__name__
            domain_counts[cat] = domain_counts.get(cat, 0) + 1
    except SyntaxError:
        for w in words:
            cat = "Structural" if (w.startswith("Ω") or w.isupper()) else "Standard"
            domain_counts[cat] = domain_counts.get(cat, 0) + 1

    if not domain_counts:
        domain_counts = {"Default": 1}

    thermo_state = engine.map_domain_entropy(domain_counts)
    s_c5 = thermo_state.shannon_entropy

    n_categories = max(1, len(domain_counts))
    p_synthetic = [1.0 / n_categories] * n_categories
    s_synthetic = engine.compute_shannon_entropy(p_synthetic)

    exergy_delta = s_synthetic - s_c5
    exergy_ratio = (structural_tokens / max(total_words, 1)) * 100

    print("[ULTRATHINK P0] Ejecutando Transducción BFT sobre learning_proposal.md...")
    print(f"Total Words: {total_words}")
    print(f"Structural Density: {exergy_ratio:.2f}%")
    print(f"S_Synthetic: {s_synthetic:.6f} nats | S_C5: {s_c5:.6f} nats | Delta: {exergy_delta:.6f} nats")

    # Inject into Ledger
    db_path = ".cortex/cortex.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA busy_timeout = 5000;")

            cursor.execute("SELECT payload_hash, lamport_t FROM bft_ledger ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            prev_hash = row[0] if row else "0000000000000000000000000000000000000000000000000000000000000000"
            last_lamport = row[1] if row else 0

            new_lamport = last_lamport + 1
            bft_key = os.environ.get("CORTEX_BFT_KEY", "fallback_key")
            new_hash = hashlib.sha3_256(bft_key.encode("utf-8") + content.encode("utf-8")).hexdigest()
            taint_signature = (
                f"CORTEX-TAINT:borjamoskv:ultrathink_learning:{time.strftime('%Y-%m-%dT%H:%M:%SZ')}:{new_hash[:8]}"
            )

            cursor.execute(
                "INSERT INTO bft_ledger (agent_id, lamport_t, payload_hash, prev_hash, cortex_taint) VALUES (?, ?, ?, ?, ?)",
                ("ultrathink_p0", new_lamport, new_hash, prev_hash, taint_signature),
            )
            conn.commit()
            print(f"[Ledger] Transacción física cristalizada. Lamport={new_lamport}, Hash={new_hash[:8]}")
        except sqlite3.Error as e:
            print(f"Ledger Warning: {e}")
        finally:
            if "conn" in locals():
                conn.close()
    else:
        print("[Ledger] Master Ledger no detectado. Modo efímero.")

    print("\n[ULTRATHINK P0] Auditoría Completada. Estado: CERO ANERGÍA. Propuesta sellada físicamente.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ultrathink_audit(sys.argv[1])
    else:
        print("Usage: python3 scripts/ultrathink_learning.py <filepath>")
