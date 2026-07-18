#!/usr/bin/env python3
"""
[C5-REAL] Exergy Optimizer Agent.
Parses changes, evaluates them using the GELABP thermodynamic framework,
and enforces code improvements to maximize exergy across iterations.
"""
import os
import sys
import re
import sqlite3
import hashlib
import time
import subprocess
from pathlib import Path

# Invariants
DB_PATH = Path(os.path.expanduser("~") + "/.babylon60/exergy_agent_ledger.db")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            commit_hash TEXT NOT NULL,
            exergy_score REAL NOT NULL,
            gradient TEXT NOT NULL,
            entropy TEXT NOT NULL,
            leverage TEXT NOT NULL,
            autoloop TEXT NOT NULL,
            bottleneck TEXT NOT NULL,
            verdict_yaml TEXT NOT NULL,
            prov_hash TEXT NOT NULL UNIQUE
        )
    """)
    conn.commit()
    conn.close()

def get_git_diff():
    try:
        # Get diff of staged and unstaged files
        diff = subprocess.check_output(
            ["git", "diff", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        )
        return diff
    except subprocess.SubprocessError:
        return ""

def evaluate_gelabp(diff_text: str):
    """
    Thermodynamic analysis of the diff.
    Computes exergy: Score = (G * L * A) / E, limited by B.
    """
    g_points = 5  # default
    e_points = 1.0
    l_points = 5
    a_points = 5
    
    reasons_g = []
    reasons_e = []
    reasons_l = []
    reasons_a = []
    
    # Analyze lines added vs removed
    added = len(re.findall(r'^\+', diff_text, re.MULTILINE))
    removed = len(re.findall(r'^\-', diff_text, re.MULTILINE))
    
    # Invariant checks:
    # 1. Broad exceptions (INV_C5_07) -> Adds Entropy
    if re.search(r'except\s+Exception\b|except\s*:', diff_text):
        e_points += 4.0
        reasons_e.append("Broad exception caught (INV_C5_07 violation).")
        
    # 2. Hardcoded secrets (INV_C5_02) -> High Entropy/Risk
    if re.search(r'(SECRET|PRIVATE_KEY|MASTER_LEDGER_KEY)\s*[:=]\s*["\']\w', diff_text, re.IGNORECASE):
        e_points += 8.0
        reasons_e.append("Hardcoded key pattern found (INV_C5_02 violation).")
        
    # 3. Weak hashes (INV_C5_03) -> High Entropy
    if re.search(r'hashlib\.(md5|sha1)\b', diff_text):
        e_points += 5.0
        reasons_e.append("Weak hashing primitives (MD5/SHA1) (INV_C5_03 violation).")

    # 4. Typing/Strict conversions (INV_C5_10) -> Increases Leverage
    if re.search(r'bytes\((sk|sk\.public_key)\)', diff_text):
        l_points += 3
        reasons_l.append("PyNaCl bytes serialization aligned with INV_C5_10.")

    # 5. Automated tests or invariant checks added -> Autocatalytic Loop
    if "test_c5_invariants" in diff_text or "autodetect_invariants" in diff_text:
        a_points += 4
        reasons_a.append("Autopoietic alignment of invariants (INV_C5_13).")

    # 6. Relative symlink checks (INV_C5_12) -> Increases Leverage
    if "readlink" in diff_text or "is_symlink" in diff_text:
        l_points += 2
        reasons_l.append("Nexus package symlink validation (INV_C5_12).")
        
    # If codebase grows too large without deletions, entropy increases
    if added > 100 and removed < 5:
        e_points += 1.5
        reasons_e.append("Large code volume increase with minimal deletion (Anergia Bloat risk).")
        
    if added > 0 and removed > added * 0.5:
        g_points += 2
        reasons_g.append("Active code pruning: high removal-to-addition ratio (Clean AST).")
        
    # Calculate raw score
    # Score = (G * L * A) / E
    raw_score = (g_points * l_points * a_points) / e_points
    # Map to [0, 1000] scale, capping max exergy at 1000
    exergy_score = min(1000.0, raw_score * 8.0)
    
    # Descriptions
    g_desc = "; ".join(reasons_g) if reasons_g else "Standard code mutation."
    e_desc = "; ".join(reasons_e) if reasons_e else "No anomalies detected."
    l_desc = "; ".join(reasons_l) if reasons_l else "Standard support abstraction."
    a_desc = "; ".join(reasons_a) if reasons_a else "Execution feedback loops intact."
    b_desc = "Disk I/O and interpreter speed limits execution."
    
    return exergy_score, g_desc, e_desc, l_desc, a_desc, b_desc

def main():
    print("🔋 Igniting C5-REAL Exergy Optimizer Agent...")
    init_db()
    
    diff = get_git_diff()
    if not diff:
        # Check diff of last commit if no changes are active
        try:
            diff = subprocess.check_output(
                ["git", "diff", "HEAD~1", "HEAD"],
                text=True, stderr=subprocess.DEVNULL
            )
            print("ℹ️ No active changes. Analyzing last commit delta.")
        except subprocess.SubprocessError:
            print("❌ Target error: Cannot load active or historical diff.")
            sys.exit(1)
            
    exergy, g, e, l, a, b = evaluate_gelabp(diff)
    
    # Calculate commit hash
    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.SubprocessError:
        commit_hash = "unknown"
        
    # Generate cryptographic provenance signature
    timestamp = time.time()
    prov_payload = f"{timestamp}:{commit_hash}:{exergy}".encode("utf-8")
    prov_hash = hashlib.sha3_256(prov_payload).hexdigest()
    
    # Build YAML verdict
    verdict_yaml = f"""# GELABP MATRIX O-COLLAPSE
Target: "Teorema-Robinson-Moskv"
Confidence: C5-REAL
ExergyScore: {exergy:.1f}/1000.0

# INVARIANTES ESTRUCTURALES
G_Gradient: |
  {g}
E_Entropy: |
  {e}
L_Leverage: |
  {l}
A_AutoLoop: |
  {a}
B_Bottleneck: |
  {b}
P_PostHoc: |
  "Narrativa descriptiva sin código" -> [TACHADO - IGNORAR]

# ATTESTATION PROVENANCE
Timestamp: {timestamp}
CommitHash: "{commit_hash}"
ProvSignature: "{prov_hash}"
"""
    print(verdict_yaml)
    
    # Write to database
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ledger (timestamp, commit_hash, exergy_score, gradient, entropy, leverage, autoloop, bottleneck, verdict_yaml, prov_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (timestamp, commit_hash, exergy, g, e, l, a, b, verdict_yaml, prov_hash))
        conn.commit()
        conn.close()
        print(f"✅ Exergy Attestation successfully written to Ledger: {DB_PATH.name}")
    except sqlite3.Error as err:
        print(f"❌ Failed to persist ledger: {err}")
        
    # Fail-Fast if exergy score is below threshold (700)
    if exergy < 700.0:
        print(f"🚨 ALERT: Iteration Exergy too low ({exergy:.1f}/1000.0). Purge entropy before committing.")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
