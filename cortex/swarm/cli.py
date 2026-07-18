"""
C5-REAL Sovereign Swarm CLI Harness
Interfaz de comandos unificada para orquestación, auditoría y control de desastres del Swarm.
"""
import os
import argparse
from cortex.swarm.engine_fsm import run_fsm_cycle
from cortex.swarm.architect_agent import ArchitectAgent
from cortex.swarm.memory_store import AgentMemory

def main() -> None:
    parser = argparse.ArgumentParser(description="MOSKV-1 Sovereign Swarm CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcomando run
    subparsers.add_parser("run", help="Ejecuta un ciclo FSM determinista completo.")

    # Subcomando audit
    audit_parser = subparsers.add_parser("audit", help="Ejecuta una auditoría de complejidad ciclomática del AST.")
    audit_parser.add_argument("--threshold", type=int, default=10, help="Umbral de complejidad máxima permitida.")

    # Subcomando kill-switch
    subparsers.add_parser("kill", help="Activa el Kill Switch físico local mediante kill_switch.lock.")
    subparsers.add_parser("unkill", help="Desactiva el Kill Switch físico eliminando kill_switch.lock.")

    # Subcomando logs
    subparsers.add_parser("logs", help="Muestra los últimos registros de auditoría del Master Ledger.")

    args = parser.parse_args()

    if args.command == "run":
        run_fsm_cycle()
    elif args.command == "audit":
        agent = ArchitectAgent()
        agent.trigger_refactoring(threshold=args.threshold)
    elif args.command == "kill":
        with open("kill_switch.lock", "w") as f:
            f.write("KILLED_BY_OPERATOR_CLI\n")
        print("[CLI] Kill Switch activado físicamente (kill_switch.lock creado).")
    elif args.command == "unkill":
        if os.path.exists("kill_switch.lock"):
            os.remove("kill_switch.lock")
            print("[CLI] Kill Switch desactivado (kill_switch.lock eliminado).")
        else:
            print("[CLI] Kill Switch no estaba activo.")
    elif args.command == "logs":
        memory = AgentMemory()
        records = memory.query_similar("")
        print("=== BFT MASTER LEDGER RECENT DECISIONS ===")
        for r in records:
            print(r)

if __name__ == "__main__":
    main()
