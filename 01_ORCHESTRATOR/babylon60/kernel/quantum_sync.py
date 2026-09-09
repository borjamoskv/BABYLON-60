# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ QUANTUM SYNC NATIVE ENGINE | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
quantum_sync.py — Native Jujutsu / Git Multi-Repo Quantum Sync Engine for BABYLON-60.
Transduced from CORTEX skills into native Python CLI execution.
"""

import argparse
import os
import subprocess
from typing import Any, Dict

class QuantumSyncEngine:
    """Atomic VCS state sync engine supporting Jujutsu (jj) and Git DAGs."""
    
    def __init__(self, repo_root: Optional[str] = None):
        self.repo_root = repo_root or os.getcwd()

    def check_vcs_status(self) -> Dict[str, Any]:
        """Audit local repository VCS configuration."""
        is_git = os.path.exists(os.path.join(self.repo_root, ".git"))
        is_jj = os.path.exists(os.path.join(self.repo_root, ".jj"))
        
        status = {
            "path": self.repo_root,
            "is_git": is_git,
            "is_jj": is_jj,
            "jj_installed": self._has_binary("jj"),
            "git_installed": self._has_binary("git"),
        }
        return status

    def _has_binary(self, name: str) -> bool:
        try:
            res = subprocess.run([name, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res.returncode == 0
        except FileNotFoundError:
            return False

    def sync(self, track_bookmark: str = "main@origin") -> Dict[str, Any]:
        """Execute atomic sync operation using jj or git."""
        vcs = self.check_vcs_status()
        results = {"status": vcs, "actions": []}
        
        if vcs["is_jj"] and vcs["jj_installed"]:
            # Perform Jujutsu sync
            cmd = ["jj", "git", "fetch"]
            res = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True)
            results["actions"].append({
                "vcs": "jj",
                "command": "jj git fetch",
                "returncode": res.returncode,
                "output": res.stdout or res.stderr
            })
            
            # Track bookmark if requested
            cmd_track = ["jj", "bookmark", "track", track_bookmark]
            res_track = subprocess.run(cmd_track, cwd=self.repo_root, capture_output=True, text=True)
            results["actions"].append({
                "vcs": "jj",
                "command": f"jj bookmark track {track_bookmark}",
                "returncode": res_track.returncode,
                "output": res_track.stdout or res_track.stderr
            })
        elif vcs["is_git"] and vcs["git_installed"]:
            # Fallback to standard git fetch
            cmd = ["git", "fetch", "--all"]
            res = subprocess.run(cmd, cwd=self.repo_root, capture_output=True, text=True)
            results["actions"].append({
                "vcs": "git",
                "command": "git fetch --all",
                "returncode": res.returncode,
                "output": res.stdout or res.stderr
            })
        else:
            results["actions"].append({
                "error": "No valid VCS workspace or executable found."
            })
            
        return results

def main():
    parser = argparse.ArgumentParser(description="BABYLON-60 Native Quantum Sync Engine")
    parser.add_argument("--status", action="store_true", help="Audit local VCS status")
    parser.add_argument("--sync", action="store_true", help="Execute atomic fetch and bookmark sync")
    args = parser.parse_args()

    engine = QuantumSyncEngine()
    
    if args.status or not args.sync:
        status = engine.check_vcs_status()
        print(f"[QUANTUM_SYNC] Workspace: {status['path']}")
        print(f"               Jujutsu Repo: {status['is_jj']} | Git Repo: {status['is_git']}")
        print(f"               jj binary: {status['jj_installed']} | git binary: {status['git_installed']}")
        
    if args.sync:
        print("[QUANTUM_SYNC] Executing atomic quantum sync...")
        res = engine.sync()
        for act in res["actions"]:
            print(f" -> [{act.get('vcs', 'vcs').upper()}] {act.get('command')}: exit code {act.get('returncode')}")

if __name__ == "__main__":
    main()
