# C5-REAL EXERGY CERTIFIED
import time
import subprocess
import os
import sys


def get_repo_path() -> str:
    # Asume que este archivo está en cortex/swarm/
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_sentinel() -> None:
    repo_path = get_repo_path()
    os.chdir(repo_path)

    print(f"[BFT_SENTINEL] Invocando demonio autónomo C5-REAL en {repo_path}")
    print("[BFT_SENTINEL] Monitorizando exergía no colapsada cada 5 segundos...")

    while True:
        try:
            # 1. Chequeamos si hay cambios (tracked o untracked)
            status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)

            mutations = status.stdout.strip()

            if mutations:
                print(f"[BFT_SENTINEL] Mutación termodinámica detectada:\n{mutations}")
                print("[BFT_SENTINEL] Ejecutando colapso de onda (BFT State Loop)...")

                # 2. Forzar colapso de estado
                subprocess.run(["git", "add", "."], check=True)

                commit_msg = "chore(bft): autonomous state collapse [C5-REAL]"
                subprocess.run(["git", "commit", "-m", commit_msg], check=True)

                new_hash = subprocess.run(
                    ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
                ).stdout.strip()

                print(f"[BFT_SENTINEL] Estado consolidado físicamente. Ledger Hash: {new_hash}")

        except subprocess.CalledProcessError as e:
            print(f"[BFT_SENTINEL] Fricción en subproceso git: {e}")
        except Exception as e:
            print(f"[BFT_SENTINEL] Error en transducción: {e}")

        # 3. Termodinámica: Prevenir saturación de I/O
        time.sleep(5)


if __name__ == "__main__":
    # Prevenir ejecución si no estamos en un repo git
    if not os.path.isdir(os.path.join(get_repo_path(), ".git")):
        print("[BFT_SENTINEL] Error: No se encontró ledger Git en la raíz.")
        sys.exit(1)

    run_sentinel()
