#!/usr/bin/env python3
"""
CORTEX OMEGA PURGE (C5-REAL)
Vector de Aniquilación Entrópica para Repositorios Locales y de Nube.
"""
import os
import subprocess
import shutil
import hashlib
from datetime import datetime, timezone

TARGET_DIRS = [
    os.path.expanduser("~/borjamoskv"),
    os.path.expanduser("~/10_PROJECTS")
]

def find_git_repos(base_dirs: list[str]) -> list[str]:
    repos = []
    for base in base_dirs:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            if '.git' in dirs:
                repos.append(root)
                dirs.remove('.git') # No bajar más allá del repo
    return repos

def obliterate_repo_entropy(repo_path: str) -> int:
    print(f"\n[OMEGA-PURGE] Iniciando colapso entrópico en: {repo_path}")
    os.chdir(repo_path)
    
    # 1. BFT Cloud Sync (Fetch & Prune)
    try:
        print("  -> Ejecutando Git Fetch --all --prune (Cloud Drift Annihilation)...")
        subprocess.run(["git", "fetch", "--all", "--prune"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("  [!] Falla en Fetch. Repositorio posiblemente sin remotos o red inaccesible.")

    # 2. Erradicación de Ramas Huérfanas
    try:
        res = subprocess.run(["git", "branch", "-vv"], capture_output=True, text=True, check=True)
        for line in res.stdout.splitlines():
            if ": gone]" in line:
                branch_name = line.split()[0]
                if branch_name.startswith("*"):
                    branch_name = branch_name[1:].strip()
                print(f"  -> Aniquilando rama huérfana local: {branch_name}")
                subprocess.run(["git", "branch", "-D", branch_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass

    # 3. Colapso Físico (Git GC Aggressive)
    try:
        print("  -> Comprimiendo objetos huérfanos (Git GC Aggressive)...")
        subprocess.run(["git", "gc", "--aggressive", "--prune=now"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("  [!] Falla estructural durante git gc.")

    # 4. Purga de Cachés Python
    purged_bytes = 0
    for root, dirs, files in os.walk(repo_path):
        for cache_dir in ["__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"]:
            if cache_dir in dirs:
                d_path = os.path.join(root, cache_dir)
                try:
                    for dr, _, fls in os.walk(d_path):
                        for f in fls:
                            purged_bytes += os.path.getsize(os.path.join(dr, f))
                    shutil.rmtree(d_path)
                    print(f"  -> Destruido: {d_path}")
                except Exception:
                    pass
                dirs.remove(cache_dir)
                
    return purged_bytes

def main() -> None:
    print("=== INICIANDO OBLITERATOR OMEGA NODE: PURGA DE ENTROPÍA MASIVA ===")
    repos = find_git_repos(TARGET_DIRS)
    print(f"Detectados {len(repos)} repositorios para aniquilación termodinámica.")
    
    total_purged_bytes = 0
    for repo in repos:
        total_purged_bytes += obliterate_repo_entropy(repo)
        
    print("\n[RESULTADO C5-REAL] Operación completada.")
    print(f"Total de entropía (cachés) evaporada físicamente: {total_purged_bytes / (1024*1024):.2f} MB")
    
    # Escribir reporte anclado
    report = f"""Claim: Purga de entropía global completada.
Proof: {{ Repos_Analyzed: {len(repos)}, Cache_Evaporated_MB: {total_purged_bytes / (1024*1024):.2f}, Timestamp: {datetime.now(timezone.utc).isoformat()} }}
Confidence: C5-REAL"""
    
    taint = hashlib.sha3_256(report.encode('utf-8')).hexdigest()
    report += f"\nCORTEX_TAINT: {taint}\n"
    
    original_cwd = os.environ.get("PWD", os.getcwd())
    os.chdir(original_cwd)
    with open("ANERGY_TOKEN_PURGE_REPORT.md", "w") as f:
        f.write(report)
        
if __name__ == "__main__":
    main()
