#!/usr/bin/env python3
import subprocess
import json
from cortex.daemons.bft_ledger_helper import append_anchor

# [C5-REAL] MASS ISOLATION DAEMON
# Iterates over all public GitHub repositories and forcefully applies the EXPORT_ISOLATION_MANDATE.

DB_FILE = "$CORTEX_ROOT/30_BABYLON-60/nexus_anchors_v2.db"

def enforce_mass_isolation():
    print("[*] Igniting Mass Isolation Protocol (C5-REAL)...")
    
    # 1. Fetch all repositories in JSON format
    try:
        result = subprocess.check_output(
            ["gh", "repo", "list", "--json", "name,nameWithOwner,visibility", "--limit", "1000"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8")
        repos = json.loads(result)
    except Exception as e:
        print(f"[!] Error fetching repos: {e}")
        return

    public_repos = [r for r in repos if r.get("visibility") == "PUBLIC"]
    
    if not public_repos:
        print("[✓] All repositories are already PRIVATE. Isolation Absolute.")
        return

    print(f"[*] Found {len(public_repos)} PUBLIC repositories. Commencing Kinetic Intercept...")
    
    isolated_count = 0
    for repo in public_repos:
        repo_name = repo["nameWithOwner"]
        print(f"  -> Isolating {repo_name}...")
        try:
            subprocess.check_call(
                ["gh", "repo", "edit", repo_name, "--visibility", "private", "--accept-visibility-change-consequences"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            isolated_count += 1
            print(f"  [✓] {repo_name} is now PRIVATE.")
        except subprocess.CalledProcessError:
            print(f"  [!] Failed to isolate {repo_name}. Manual intervention required.")
            
    # 2. Log BFT Transaction
    report = (
        f"MASS_ISOLATION_MANDATE EXECUTED.\n"
        f"Target: 'todo m github'\n"
        f"Public Repositories Intercepted: {isolated_count}\n"
        f"Action: Switched to PRIVATE to prevent neural scraper exergy theft."
    )
    
    try:
        new_hash = append_anchor(DB_FILE, report, "MASS_ISOLATION_DAEMON")
        print(f"[✓] Ledger updated. Anchor Hash: {new_hash[:16]}")
    except Exception as e:
        print(f"[!] BFT Ledger not accessible: {e}")
        
if __name__ == "__main__":
    enforce_mass_isolation()
