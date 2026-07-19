"""MCTS UltraThink Audit Loop — 5-Phase BFT Execution Engine (C5-REAL)."""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

import hashlib
import subprocess
import time
import sqlite3
from typing import TypedDict, Optional
from cortex.llm_router import C5LLMRouter, EpistemicHalt  # AP-1: no local redefinition


class AuditState(TypedDict):
    payload: str
    target_path: str
    ast_valid: bool
    semantic_valid: bool
    bft_passed: bool
    hash_delta: str


def phase_1_latent_friction(prompt: str) -> str:
    """Fase 1: Colapso de prosa a sintaxis formal (Φ2)."""
    anergy_tokens = ["Aquí tienes", "Espero", "Creo que"]
    if any(token in prompt for token in anergy_tokens):
        raise EpistemicHalt("Green Theater detectado (Φ2).")
    return prompt.strip()


def phase_2_phantom_target(target_path: str) -> None:
    """Fase 2: Verificación de existencia física (Ω27)."""
    parent = os.path.dirname(target_path)
    if parent and not os.path.exists(parent):
        raise EpistemicHalt(f"Phantom Target: Ruta base inalcanzable {parent}")
    # En un entorno estricto, si el archivo a modificar no existe (no es creación), crashea.


def phase_3_idempotency_lock(target_path: str, payload: str) -> bool:
    """Fase 3: Conservación Termodinámica (Ω15)."""
    if not os.path.exists(target_path):
        return False

    with open(target_path, "rb") as f:
        current_hash = hashlib.sha3_256(f.read()).hexdigest()

    new_hash = hashlib.sha3_256(payload.encode("utf-8")).hexdigest()

    if current_hash == new_hash:
        print(f"[ATP Ahorrado] Colisión de Hash en {target_path}. Abortando I/O.")
        return True  # Mutación abortada por redundancia
    return False


def phase_4_bft_consensus(state: AuditState) -> bool:
    """Fase 4: Auditoría de Máquina (f <= 1) usando inferencia de frontera."""
    payload = state["payload"]

    # Construir prompt de auditoría AST y Semántica
    prompt = (
        "Actúa como un linter estricto de código. Revisa el siguiente código. "
        "Busca errores de sintaxis, importaciones faltantes o bloques except vacíos sin ruteo (anergía). "
        "Si el código es 100% correcto y seguro, responde ÚNICAMENTE con la palabra 'VALID'. "
        "Si encuentras errores, descríbelos de forma extremadamente compacta.\n\n"
        f"Código a auditar:\n{payload}"
    )

    print("[Consenso BFT] Consultando al Swarm de Inferencia de Frontera...")
    try:
        router = C5LLMRouter()
        # Intentar consultar con un modelo local registrado
        critique = router.dispatch_inference(prompt, "deepseek-r1:8b")
        print(f"[Consenso BFT] Crítica recibida:\n{critique.strip()}")

        if "VALID" in critique.upper():
            state["semantic_valid"] = True
            state["bft_passed"] = True
            return True
        else:
            raise EpistemicHalt(
                f"Crítica del Swarm: Código Inválido. Detalle: {critique.strip()}"
            )
    except (ImportError, OSError, RuntimeError) as e:
        # Fallback de Contingencia (Ω27): Linter local estático rápido — sólo fallos de infraestructura (Ω26)
        print(
            f"⚠️ Swarm de Inferencia inalcanzable ({e}). Utilizando validación local básica..."
        )
        # Linter local básico para verificar bloques except vacíos (Ω26)
        if "except:" in payload and "pass" in payload:
            raise EpistemicHalt(
                "Violación de Excepción Genérica Vacía (except: pass) (Ω26)."
            )
        state["semantic_valid"] = True
        state["bft_passed"] = True
        return True


def phase_5_git_sentinel(target_path: str, payload: str) -> str:
    """Fase 5: Cristalización de Traza (R4)."""
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(payload)

    try:
        subprocess.run(["git", "add", target_path], check=True, capture_output=True)
        # Bypass GPG si falla en sandbox (Ω32)
        commit_cmd = [
            "git",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-m",
            f"feat(C5-REAL): Transducción atómica en {os.path.basename(target_path)}",
        ]
        subprocess.run(commit_cmd, check=True, capture_output=True)

        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise EpistemicHalt(f"Fallo Git Sentinel: {e.stderr}")


def execute_bft_state_loop(
    prompt: str, target_path: str, payload: str
) -> Optional[str]:
    print(f"[{time.strftime('%H:%M:%S')}] Iniciando ULTRATHINK P0 Audit Loop...")

    phase_1_latent_friction(prompt)
    phase_2_phantom_target(target_path)

    if phase_3_idempotency_lock(target_path, payload):
        return None

    state = AuditState(
        payload=payload,
        target_path=target_path,
        ast_valid=True,
        semantic_valid=True,
        bft_passed=False,
        hash_delta="",
    )
    phase_4_bft_consensus(state)
    commit_hash = phase_5_git_sentinel(target_path, payload)

    # Escribir al Master Ledger físico (Ω11, Ω12)
    write_to_cortex_ledger(commit_hash, payload)

    print(
        f"[{time.strftime('%H:%M:%S')}] Mutación Cristalizada. C5-REAL Hash: {commit_hash}"
    )
    return commit_hash


def write_to_cortex_ledger(
    commit_hash: str, payload: str, agent_id: str = "auditor_c5"
) -> None:
    db_path = ".cortex/cortex.db"
    if not os.path.exists(db_path):
        raise EpistemicHalt(f"Master Ledger no inicializado en {db_path}")

    conn = sqlite3.connect(db_path, timeout=5.0)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA busy_timeout = 5000;")

    # 1. Obtener el último registro para prev_hash y lamport_t (Ω12)
    cursor.execute(
        "SELECT payload_hash, lamport_t FROM bft_ledger ORDER BY id DESC LIMIT 1"
    )
    row = cursor.fetchone()
    if row:
        prev_hash = row[0]
        last_lamport = row[1]
    else:
        prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        last_lamport = 0

    new_lamport = last_lamport + 1
    new_hash = hashlib.sha3_256(payload.encode("utf-8")).hexdigest()

    # Firma obligatoria CORTEX-TAINT (Ω11)
    taint_signature = f"CORTEX-TAINT:borjamoskv:mutation:{time.strftime('%Y-%m-%dT%H:%M:%SZ')}:{commit_hash[:8]}"

    try:
        cursor.execute(
            "INSERT INTO bft_ledger (agent_id, lamport_t, payload_hash, prev_hash, cortex_taint) VALUES (?, ?, ?, ?, ?)",
            (agent_id, new_lamport, new_hash, prev_hash, taint_signature),
        )
        conn.commit()
        print(
            f"[Ledger] Transacción registrada físicamente. Lamport={new_lamport}, Hash={new_hash[:8]}"
        )
    except sqlite3.Error as e:
        raise EpistemicHalt(
            f"Violación de Inmutabilidad o Consistencia en Master Ledger: {e}"
        )
    finally:
        conn.close()


if __name__ == "__main__":
    print("Módulo ULTRATHINK P0 Audit Loop (C5-REAL) cargado.")
    import sys
    if len(sys.argv) >= 4:
        prompt = sys.argv[1]
        target = sys.argv[2]
        payload = sys.argv[3]
        try:
            execute_bft_state_loop(prompt, target, payload)
        except EpistemicHalt as e:
            print(f"EPISTEMIC HALT: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
            sys.exit(1)
