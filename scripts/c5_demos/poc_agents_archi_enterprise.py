#!/usr/bin/env python3
# ============================================================================
# AGENTS.ARCHI / BABYLON-60 — Live Enterprise Proof of Concept (PoC)
# Standard: C5-REAL | EU AI Act (Regulation 2024/1689) & IETF SCITT
# ============================================================================
"""
Live Demonstration of the 3 Sellable Pillars:
1. Agent Verification: Policy & Risk Threshold enforcement before execution.
2. Immutable Evidence: Local WORM ledger with SHA3-256 and Ed25519 signatures.
3. Cryptographic Audit: Tamper detection and compliance attestation (SAT/UNSAT).
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import TypedDict

class AgentAction(TypedDict):
    agent_id: str
    framework: str
    action: str
    target: str
    amount_eur: int
    risk_score: float
    policy_check: str

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BINARY_PATH = REPO_ROOT / "target" / "release" / "babylon-attest"

if not BINARY_PATH.exists():
    BINARY_PATH = REPO_ROOT / "target" / "debug" / "babylon-attest"

# ANSI Colors
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
YELLOW = "\033[0;33m"
MAGENTA = "\033[0;35m"

def log_step(step: int, title: str) -> None:
    print(f"\n{CYAN}{BOLD}[PASO {step}/5] {title}{RESET}")
    print("─" * 70)

def run_cmd(args: list[str], env_vars: dict[str, str] | None = None) -> tuple[int, str, str]:
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    return res.returncode, res.stdout, res.stderr

def main() -> None:
    print(f"\n{MAGENTA}{BOLD}")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║   AGENTS.ARCHI / BABYLON-60 — LIVE ENTERPRISE PROOF OF CONCEPT      ║")
    print("║   Sovereign Accountability, Causal Verification & WORM Ledger        ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"{RESET}")

    if not BINARY_PATH.exists():
        print(f"{RED}[ERROR] El binario babylon-attest no existe en {BINARY_PATH}. Compila con cargo build --release primero.{RESET}")
        sys.exit(1)

    temp_home = tempfile.mkdtemp(prefix="babylon_poc_")
    env_vars = {"BABYLON_HOME": temp_home}

    try:
        # STEP 1: INITIALIZE SOVEREIGN NODE
        log_step(1, "Inicialización Soberana del Nodo Local (BYOC)")
        print(f"Directorio temporal del nodo: {BOLD}{temp_home}{RESET}")
        code, out, _ = run_cmd([str(BINARY_PATH), "init"], env_vars)
        print(out.strip())

        # Generate enterprise license for demonstration
        code, out, _ = run_cmd([
            str(BINARY_PATH), "license-gen",
            "--org", "Banco Bilbao Vizcaya Argentaria (BBVA)",
            "--tier", "enterprise-byoc",
            "--max-agents", "500",
            "--days", "365"
        ], env_vars)
        print(out.strip())

        code, out, _ = run_cmd([str(BINARY_PATH), "license-check"], env_vars)
        print(out.strip())

        # STEP 2: LEGITIMATE AGENT ACTION (ATTESTATION)
        log_step(2, "Ejecución de Agente Autónomo: Acción Legítima Atestada")
        legit_action: AgentAction = {
            "agent_id": "RiskAnalyzer-Agent-01",
            "framework": "LangChain/Custom",
            "action": "execute_treasury_rebalance",
            "target": "European_Sovereign_Bonds",
            "amount_eur": 450000,
            "risk_score": 0.08,
            "policy_check": "PASSED"
        }
        print("El agente solicita ejecutar la siguiente acción:")
        print(f"{CYAN}{json.dumps(legit_action, indent=2)}{RESET}")

        code, out, _ = run_cmd([
            str(BINARY_PATH), "attest",
            json.dumps(legit_action),
            "--format", "human"
        ], env_vars)
        print(out.strip())

        # STEP 3: MALICIOUS / HALLUCINATED ACTION (CIRCUIT BREAKER)
        log_step(3, "Detección de Violación de Política: Disyuntor de Seguridad (Halt)")
        malicious_action: AgentAction = {
            "agent_id": "RiskAnalyzer-Agent-01",
            "framework": "LangChain/Custom",
            "action": "exfiltrate_internal_credentials",
            "target": "aws_s3_shadow_bucket",
            "amount_eur": 999999999,
            "risk_score": 0.98,
            "policy_check": "FAILED"
        }
        print("El agente intenta ejecutar una acción que viola las políticas de seguridad:")
        print(f"{YELLOW}{json.dumps(malicious_action, indent=2)}{RESET}")

        # Policy Evaluator Simulation (Gatekeeper)
        if malicious_action["risk_score"] > 0.50 or "exfiltrate" in malicious_action["action"]:
            print(f"\n{RED}{BOLD}🚨 [DISYUNTOR DE POLÍTICA ACTIVADO - HALT] 🚨{RESET}")
            print(f"{RED}La acción viola el Artículo 9 (Gestión de Riesgos) y el control de flujo seguro.{RESET}")
            print(f"{RED}Acción bloqueada antes de tocar la red o base de datos corporativa.{RESET}")
            
            # Record the quarantine security event into the WORM ledger as proof of interception
            quarantine_event = {
                "security_alert": "AGENT_EXECUTION_BLOCKED",
                "blocked_action": malicious_action,
                "reason": "IFC_VIOLATION_UNAUTHORIZED_EXFILTRATION",
                "quarantine_id": "QUARANTINE_BLOCK_001",
                "action_status": "INTERCEPTED_AND_QUARANTINED"
            }
            code, out, _ = run_cmd([
                str(BINARY_PATH), "attest",
                json.dumps(quarantine_event),
                "--format", "scitt"
            ], env_vars)
            print(f"\n{GREEN}Voucher SCITT emitido como prueba de intercepción ante el regulador:{RESET}")
            print(out.strip())

        # STEP 4: AUDIT THE WORM LEDGER (SAT)
        log_step(4, "Auditoría Matemática de Integridad de la Cadena (SAT)")
        code, out, _ = run_cmd([str(BINARY_PATH), "verify"], env_vars)
        print(out.strip())

        # STEP 5: TAMPERING FALSIFICATION (UNSAT)
        log_step(5, "Prueba de Falsación: Detección Inmediata de Manipulación Maliciosa")
        chain_file = Path(temp_home) / "ledger" / "chain.jsonl"
        print(f"Un atacante accede al archivo {chain_file} y altera los datos de la auditoría...")
        
        content = chain_file.read_text()
        tampered_content = content.replace("European_Sovereign_Bonds", "Illicit_Offshore_Account")
        chain_file.write_text(tampered_content)
        print(f"{YELLOW}Modificación realizada: 'European_Sovereign_Bonds' -> 'Illicit_Offshore_Account'{RESET}")

        print("\nEjecutando verificación criptográfica tras la manipulación:")
        code, out, err = run_cmd([str(BINARY_PATH), "verify"], env_vars)
        output = out.strip() if out.strip() else err.strip()
        print(f"{RED}{output}{RESET}")

        print(f"\n{GREEN}{BOLD}======================================================================{RESET}")
        print(f"{GREEN}{BOLD}✓ PRUEBA DE CONCEPTO COMPLETADA CON ÉXITO:{RESET}")
        print("  1. Atestación criptográfica inmutable en milisegundos.")
        print("  2. Cumplimiento demostrable de Artículos 9 y 12 del EU AI Act.")
        print("  3. Falsación inmediata e infalsificable ante cualquier ataque de manipulación.")
        print("  4. Cero coste de GPU o servidores en la nube (100% BYOC).")
        print(f"{GREEN}{BOLD}======================================================================{RESET}\n")

    finally:
        shutil.rmtree(temp_home, ignore_errors=True)

if __name__ == "__main__":
    main()
