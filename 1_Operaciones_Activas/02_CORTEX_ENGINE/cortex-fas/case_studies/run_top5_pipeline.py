# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
FAS v24 — HVT Pipeline Orchestrator
Reality level: C5-REAL
Aesthetics: Industrial Noir 2026

Extracts TOP 5 targets from the massive CRONOS ledger and forces
the entire pipeline (OSINT -> Acta -> Red-Team) to execute on them.
"""

import json
import os
import subprocess
import sys

def main():
    base_dir = os.path.dirname(__file__)
    cronos_ledger = os.path.join(base_dir, "bizkaia_cronos_ledger.jsonl")
    training_ledger = os.path.join(base_dir, "bizkaia_training_ledger.jsonl")

    if not os.path.exists(cronos_ledger):
        print("[-] CRONOS ledger missing.")
        sys.exit(1)

    # 1. Load CRONOS and get TOP 5
    records = []
    with open(cronos_ledger, 'r') as f:
        for line in f:
            if line.strip():
                try: records.append(json.loads(line))
                except Exception: pass

    if not records:
        print("[-] No records found.")
        sys.exit(1)

    sorted_records = sorted(records, key=lambda x: x.get("financials", {}).get("total_due_eur", 0), reverse=True)
    top_5 = sorted_records[:5]

    # 2. Overwrite training ledger
    with open(training_ledger, 'w') as f:
        for r in top_5:
            f.write(json.dumps(r) + "\n")

    print("[*] Injected TOP 5 HVT from CRONOS into training ledger.")

    # 3. Run Pipeline
    print("\n[+] RUNNING OSINT MINER...")
    subprocess.run(["python3", "ens_osint_miner.py"], cwd=base_dir)

    print("\n[+] RUNNING ACTA GENERATOR...")
    subprocess.run(["python3", "run_inspection_report.py"], cwd=base_dir)

    print("\n[+] RUNNING RED-TEAM ADVERSARIAL ENGINE...")
    subprocess.run(["python3", "run_adversarial_redteam.py"], cwd=base_dir)

    print("\n[*] HVT PIPELINE COMPLETE. Verification artifacts compiled.")

if __name__ == "__main__":
    main()
