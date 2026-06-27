#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from pathlib import Path
from colorama import init, Fore, Style

init(autoreset=True)

C5_RED = Fore.RED
C5_BLUE = Fore.BLUE
C5_DIM = Style.DIM

print(f"{C5_BLUE}[C5-REAL] CAOS-Ω (Cybernetic Autonomous Ordering System){Style.RESET_ALL}")
print(f"{C5_DIM}Axiom: Ω₂ Entropic Asymmetry — Order displaces chaos aggressively.{Style.RESET_ALL}")
print(f"{C5_RED}Initiating Phase 1: Thermodynamic Scan...{Style.RESET_ALL}\n")

home_dir = Path.home()
projects_dir = home_dir / "10_PROJECTS"
scratch_dir = home_dir / "70_SCRATCH"
archive_dir = home_dir / "99_ARCHIVE"

# Ensure dirs exist
for d in [projects_dir, scratch_dir, archive_dir]:
    if not d.exists():
        d.mkdir(parents=True, exist_ok=True)

def run_cmd(cmd, cwd=None):
    try:
        res = subprocess.run(cmd, cwd=cwd, shell=True, text=True, capture_output=True)
        return res.stdout.strip()
    except Exception as e:
        return ""

def scan_git_entropy():
    print(f"{C5_BLUE}[*] Scanning 10_PROJECTS for git entropy...{Style.RESET_ALL}")
    dirty_repos = []
    if projects_dir.exists():
        for p in projects_dir.iterdir():
            if p.is_dir() and (p / ".git").exists():
                status = run_cmd("git status --short", cwd=p)
                if status:
                    dirty_repos.append((p.name, len(status.split('\n'))))
    
    if dirty_repos:
        for r, count in dirty_repos:
            print(f"  {C5_RED}→ DIRTY REPO:{Style.RESET_ALL} {r} ({count} unstaged/untracked files)")
    else:
        print(f"  {C5_DIM}→ Zero entropy detected in git repos.{Style.RESET_ALL}")

def scan_loose_files():
    print(f"\n{C5_BLUE}[*] Scanning root ~ and 70_SCRATCH for cognitive debris...{Style.RESET_ALL}")
    debris = []
    
    # Scan root ~ for stray py/txt/json (maxdepth 1 equivalent)
    for f in home_dir.iterdir():
        if f.is_file() and f.suffix in ['.py', '.txt', '.json'] and not f.name.startswith('.'):
            debris.append(f)
            
    # Scan scratch
    if scratch_dir.exists():
        for f in scratch_dir.glob("*"):
            if f.is_file() and not f.name.startswith('.'):
                debris.append(f)
                
    if debris:
        print(f"  {C5_RED}→ DEBRIS FOUND:{Style.RESET_ALL} {len(debris)} unanchored files.")
        for d in debris[:5]:
            print(f"    - {d.relative_to(home_dir)}")
        if len(debris) > 5:
            print(f"    ... and {len(debris) - 5} more.")
    else:
        print(f"  {C5_DIM}→ Workspace pristine. No orphans found.{Style.RESET_ALL}")

def summary():
    print(f"\n{C5_BLUE}--- CAOS-Ω EXECUTION SUMMARY ---{Style.RESET_ALL}")
    print("Claim: Thermodynamic scan complete.")
    print("Proof: { Confidence: C5-REAL, Environment: Industrial Noir 2026 }")
    print("Action Required: Agent must execute `mv` and `git commit` to finalize crystallization.")

if __name__ == "__main__":
    time.sleep(0.5)
    scan_git_entropy()
    scan_loose_files()
    summary()
