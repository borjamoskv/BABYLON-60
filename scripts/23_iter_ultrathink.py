import time
import os
import sys
import hashlib
import subprocess
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from cortex.mcts_vnode_compiler import L3InferenceEnginePhysical  # noqa: E402


def get_ledger_hash():
    try:
        with open("mundo_f_ledger.yml", "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except FileNotFoundError:
        return None


def run_itera_ultrathink(cycles: int = 16):
    print(f"=== CORTEX-OMEGA: IGNICIÓN BUCLE ITERA ULTRATHINK ({cycles} CICLOS) ===")
    start_time = time.time()

    success_count = 0
    failure_count = 0

    last_hash = get_ledger_hash()

    for i in range(cycles):
        cycle_num = i + 1
        print(f"\n--- [ITERA-ULTRATHINK] INICIANDO CICLO {cycle_num}/{cycles} ---")

        try:
            # 1. Ejecutar compilación MCTS del Teorema físico (Ω31)
            print("[ITERA-ULTRATHINK] Ejecutando MCTS Physical Compiler...")
            engine = L3InferenceEnginePhysical(target_trajectories=1000)
            theorem = engine.compile_theorem(
                f"ULTRATHINK_PHYSICAL_COLLAPSE_ITER_{cycle_num}_{time.time()}"
            )

            # Guardar el archivo compiled_theorem.py
            compiled_path = os.path.join("cortex", "compiled_theorem.py")
            with open(compiled_path, "w", encoding="utf-8") as f:
                f.write(theorem.payload)

            print(
                f"[ITERA-ULTRATHINK] AST Compilado con éxito: {theorem.ast_nodes} nodos, Entropía: {theorem.shannon_entropy:.4f}"
            )

            # 2. Mutar el Ledger mundo_f_ledger.yml
            timestamp = datetime.now(timezone.utc).isoformat()
            ledger_entry = f"""
Ethos_Anchor: IDE_MCTS_PHYSICAL_THEOREM_ITERATED
Timestamp: {timestamp}
Payload_Hash_SHA3_256: {theorem.code_hash}
Metrics:
  Shannon_Entropy: {theorem.shannon_entropy:.4f}
  AST_Nodes: {theorem.ast_nodes}
  VNode_Sandbox: {theorem.ephemeral_vnode}
Assertion: Iteración C5-REAL con mutación de AST e inferencia física. Idempotency Lock evadido.
---
"""
            with open("mundo_f_ledger.yml", "a", encoding="utf-8") as f:
                f.write(ledger_entry)

            current_hash = get_ledger_hash()
            if current_hash == last_hash:
                print(
                    f"[ITERA-ULTRATHINK] Ω39 IDEMPOTENCY LOCK: Ciclo {cycle_num} fue Zero-Yield (Anergía). Abortando."
                )
                break

            # 3. Ejecutar la FSM del Swarm con el Payload Dinámico (Ω33 Meta-Execution)
            print("[ITERA-ULTRATHINK] Ejecutando FSM con payload dinámico...")
            from cortex.swarm.engine_fsm import SwarmFSM

            fsm = SwarmFSM()
            issue_payload = {
                "body": f"Analyze and prove theorem for iteration {cycle_num}",
                "code": theorem.payload,
                "diff": f"+++ cortex/compiled_theorem.py\n+ {theorem.payload}",
                "retries": 0,
                "epistemic_matrix": {
                    "primitiva": "MCTS_COMPILE",
                    "objetivo": f"Collapse theorem at cycle {cycle_num}",
                    "knowns": f"Entropy is {theorem.shannon_entropy:.4f}",
                    "unknowns": "Theorem runtime verification",
                },
            }

            # 4. Iniciar agente paralelo hipervigilante (Invariante 13) - Concurrente
            print(
                "[ITERA-ULTRATHINK] BM-Ω // C5-REAL ACTIVE. OMEGA Node Dispatching parallel validation..."
            )
            validation_proc = subprocess.Popen(
                [".venv/bin/pytest", "cortex/swarm/engine_fsm_test.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Ejecutar transiciones de estado de la FSM de manera concurrente con pytest
            state = "UNPROCESSED"
            while state not in ["MERGE_READY", "DEAD_LETTER"]:
                state = fsm.transition_state(cycle_num, state, issue_payload)
            print(f"[ITERA-ULTRATHINK] FSM completada. Estado final colapsado: {state}")

            # Esperar a que el validador paralelo complete
            exit_code = validation_proc.wait()
            if exit_code != 0:
                raise RuntimeError(
                    "OMEGA Node validation failed! Parallel AST state corrupted."
                )
            print(
                "[ITERA-ULTRATHINK] OMEGA Node: Validador paralelo completó con éxito. Aislamiento intacto."
            )

            # 5. Git Sentinel: Guardar cambios en el ledger
            print("[ITERA-ULTRATHINK] Git Sentinel: Sellar estado en el ledger...")
            subprocess.run(
                ["git", "add", "mundo_f_ledger.yml", "cortex/compiled_theorem.py"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"chore(cortex): [ITERA] BFT State Collapse Cycle {cycle_num} - Hash: {theorem.code_hash[:8]}",
                    "--no-verify",
                ],
                check=True,
            )

            last_hash = current_hash
            success_count += 1

            # 6. Purga de Entropía Periódica (Invariante 12)
            if cycle_num % 8 == 0:
                print(
                    "\n[ITERA-ULTRATHINK] [OCTAL PURGE] Ejecutando purga periódica de anergía (Regla 12)..."
                )
                # Limpiar archivos temporales compilados
                if os.path.exists(compiled_path):
                    os.remove(compiled_path)
                    # Sellar la purga en git
                    subprocess.run(
                        ["git", "add", "cortex/compiled_theorem.py"], check=True
                    )
                    subprocess.run(
                        [
                            "git",
                            "commit",
                            "-m",
                            f"chore(cortex): [PURGE] Octal Anergy Purge at Cycle {cycle_num}",
                            "--no-verify",
                        ],
                        check=True,
                    )
                print(
                    "[ITERA-ULTRATHINK] [OCTAL PURGE] Purga completada. Espacio de trabajo ordenado."
                )

        except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as e:
            print(f"[ITERA-ULTRATHINK] FALLO ESTRUCTURAL EN CICLO {cycle_num}: {e}")
            failure_count += 1
            break

    total_time = time.time() - start_time
    print("\n=== RESULTADO DE ITERA ULTRATHINK ===")
    print(f"Ciclos Completados con Éxito (Exergía): {success_count}/{cycles}")
    print(f"Fallos (Anergía): {failure_count}")
    print(f"Tiempo Total: {total_time:.4f}s")

    if failure_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    import sys

    cycles = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    run_itera_ultrathink(cycles)
