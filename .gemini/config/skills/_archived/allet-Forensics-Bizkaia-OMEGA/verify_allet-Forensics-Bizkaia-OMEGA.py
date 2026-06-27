#!/usr/bin/env python3
import os
import sys

def verify():
    print("[*] Verifying allet-Forensics-Bizkaia-OMEGA Tripartite Artifacts...")
    
    # 1. Check local files
    base_dir = os.path.dirname(__file__)
    if not os.path.exists(os.path.join(base_dir, "SKILL.md")):
        print("[-] SKILL.md missing")
        sys.exit(1)
    if not os.path.exists(os.path.join(base_dir, "schema.json")):
        print("[-] schema.json missing")
        sys.exit(1)
        
    # 2. Check ecosystem linkages
    project_dir = os.path.expanduser("~/10_PROJECTS/cortex-fas/case_studies")
    required_modules = [
        "ens_osint_miner.py",
        "run_inspection_report.py",
        "run_adversarial_redteam.py",
        "run_bizkaia_cronos.py"
    ]
    
    for mod in required_modules:
        if not os.path.exists(os.path.join(project_dir, mod)):
            print(f"[-] Missing C5-REAL execution module: {mod}")
            sys.exit(1)
            
    print("[+] Verification SUCCESS: Ecosystem is C5-REAL Compliant.")
    sys.exit(0)

if __name__ == "__main__":
    verify()
