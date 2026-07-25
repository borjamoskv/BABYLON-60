# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
CORTEX OMEGA PURGE (C5-REAL)
Vector de Aniquilación Entrópica para Repositorios Locales y de Nube.
Version: 2.0 (Parallel Execution, Atomic Write, Type-Safe)
"""

import os
import subprocess
import shutil
import hashlib
from datetime import datetime, timezone
import concurrent.futures
from typing import List

workspace_dirs = os.environ.get("CORTEX_WORKSPACE_DIRS", "").split(":")
if not workspace_dirs or workspace_dirs == [""]:
    workspace_dirs = [os.getcwd()]
TARGET_DIRS: List[str] = workspace_dirs


def find_git_repos(base_dirs: List[str]) -> List[str]:
    repos: List[str] = []
    for base in base_dirs:
        if not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            if ".git" in dirs:
                repos.append(root)
                dirs.remove(".git")  # No bajar más allá del repo
    return repos


def obliterate_repo_entropy(repo_path: str) -> int:
    print(f"[OMEGA-PURGE] Iniciando colapso entrópico en: {repo_path}")
    purged_bytes = 0

    # 1. BFT Cloud Sync (Fetch & Prune)
    try:
        subprocess.run(
            ["git", "fetch", "--all", "--prune"],
            cwd=repo_path,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print(f"  [!] {repo_path}: Falla en Fetch (posible falta de remotos).")

    # 2. Erradicación de Ramas Huérfanas
    try:
        res = subprocess.run(
            ["git", "branch", "-vv"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        for line in res.stdout.splitlines():
            if ": gone]" in line:
                branch_name = line.split()[0]
                if branch_name.startswith("*"):
                    branch_name = branch_name[1:].strip()
                print(f"  -> {repo_path}: Aniquilando rama huérfana local: {branch_name}")
                subprocess.run(
                    ["git", "branch", "-D", branch_name],
                    cwd=repo_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
    except subprocess.CalledProcessError:
        pass

    # 3. Colapso Físico (Git GC Aggressive)
    try:
        subprocess.run(
            ["git", "gc", "--aggressive", "--prune=now"],
            cwd=repo_path,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        print(f"  [!] {repo_path}: Falla estructural durante git gc.")

    # 4. Purga de Cachés Python
    for root, dirs, files in os.walk(repo_path):
        for cache_dir in ["__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"]:
            if cache_dir in dirs:
                d_path = os.path.join(root, cache_dir)
                try:
                    for dr, _, fls in os.walk(d_path):
                        for f in fls:
                            file_path = os.path.join(dr, f)
                            try:
                                purged_bytes += os.path.getsize(file_path)
                            except OSError:
                                pass
                    shutil.rmtree(d_path)
                    print(f"  -> {repo_path}: Destruido {cache_dir}")
                except OSError:
                    pass
                dirs.remove(cache_dir)

    return purged_bytes


def main() -> None:
    print("=== INICIANDO OBLITERATOR OMEGA NODE: PURGA DE ENTROPÍA MASIVA ===")
    repos = find_git_repos(TARGET_DIRS)
    print(f"Detectados {len(repos)} repositorios para aniquilación termodinámica paralela.")

    total_purged_bytes = 0

    # Ejecución paralela con mitigación del GIL
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_repo = {executor.submit(obliterate_repo_entropy, repo): repo for repo in repos}
        for future in concurrent.futures.as_completed(future_to_repo):
            try:
                purged = future.result()
                total_purged_bytes += purged
            except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
                print(f"Error procesando un repositorio: {exc}")

    print("\n[RESULTADO C5-REAL] Operación completada.")
    print(f"Total de entropía (cachés) evaporada físicamente: {total_purged_bytes / (1024 * 1024):.2f} MB")

    # Escribir reporte anclado con Atomic Write (Ω41)
    report = f"""Claim: Purga de entropía global completada de forma concurrente.
Proof: {{ Repos_Analyzed: {len(repos)}, Cache_Evaporated_MB: {total_purged_bytes / (1024 * 1024):.2f}, Timestamp: {datetime.now(timezone.utc).isoformat()} }}
Confidence: C5-REAL"""

    taint = hashlib.sha3_256(report.encode("utf-8")).hexdigest()
    report += f"\nCORTEX_TAINT: {taint}\n"

    # Ω41: Atomic file write
    original_cwd = os.environ.get("PWD", os.getcwd())
    final_path = os.path.join(original_cwd, "ANERGY_TOKEN_PURGE_REPORT.md")
    tmp_path = final_path + ".tmp"

    with open(tmp_path, "w") as f:
        f.write(report)

    os.replace(tmp_path, final_path)


if __name__ == "__main__":
    main()
