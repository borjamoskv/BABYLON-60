# C5-REAL EXERGY CERTIFIED
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from cortex.primitives.bash_primitive import BashCommand


def get_repo_path() -> str:
    curr = Path(__file__).resolve().parent
    while curr != curr.root and curr != Path("/"):
        if (curr / ".git").exists() or (curr / ".cursorrules").exists():
            return str(curr)
        curr = curr.parent
    # Fallback to current working directory or fixed depth
    return os.getcwd()


def run_sentinel() -> None:
    repo_path = get_repo_path()
    os.chdir(repo_path)

    print(f"[BFT_SENTINEL] Invocando demonio autónomo C5-REAL en {repo_path}")
    print("[BFT_SENTINEL] Monitorizando exergía no colapsada cada 5 segundos...")

    while True:
        try:
            status = BashCommand(
                binary="git",
                args=("status", "--porcelain")
            ).execute()
            mutations = status.stdout.strip()

            if mutations:
                print(f"[BFT_SENTINEL] Mutación termodinámica detectada:\n{mutations}")
                print("[BFT_SENTINEL] Ejecutando colapso de onda (BFT State Loop)...")

                BashCommand(binary="git", args=("add", ".")).execute()
                commit_msg = "chore(bft): autonomous state collapse [C5-REAL]"
                BashCommand(binary="git", args=("commit", "-m", commit_msg)).execute()

                new_hash = BashCommand(
                    binary="git",
                    args=("rev-parse", "HEAD")
                ).execute().stdout.strip()

                print(f"[BFT_SENTINEL] Estado consolidado físicamente. Ledger Hash: {new_hash}")

        except RuntimeError as e:
            print(f"[BFT_SENTINEL] Fricción en subproceso git: {e}")
        except Exception as e:
            print(f"[BFT_SENTINEL] Error en transducción: {e}")

        time.sleep(5)


if __name__ == "__main__":
    repo = get_repo_path()
    if not (Path(repo) / ".git").exists() and not (Path(repo) / ".cursorrules").exists():
        print(f"[BFT_SENTINEL] Error: No se encontró ledger Git ni .cursorrules en {repo}.")
        sys.exit(1)

    run_sentinel()

