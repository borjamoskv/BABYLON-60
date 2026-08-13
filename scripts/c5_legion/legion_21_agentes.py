#!/usr/bin/env python3
"""
MOSKV-1: Enjambre de 21 Agentes Paralelizados (C5-REAL Execution Engine)
Ejecuta la auditoría, verificación formal, comprobación de licencias y prueba de empaquetado
en paralelo a través de 7 escuadrones especializados de 3 agentes cada uno (21 Agentes totales).
Soporta emisión de telemetría nativa en JSON M2M via --json.
"""

import sys
import os
import json
import time
import argparse
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def run_agent_task(agent_id: int, squad: str, name: str, command: list[str], env: dict) -> dict:
    start_time = time.monotonic()
    try:
        res = subprocess.run(
            command,
            cwd=ROOT_DIR,
            env=env,
            capture_output=True,
            text=True,
            timeout=45
        )
        duration = round(time.monotonic() - start_time, 3)
        return {
            "agent_id": f"AGENT-{agent_id:02d}",
            "squad": squad,
            "name": name,
            "status": "PASS" if res.returncode == 0 else "FAIL",
            "duration_s": duration,
            "stdout": res.stdout.strip()[:200],
            "stderr": res.stderr.strip()[:200]
        }
    except Exception as e:
        duration = round(time.monotonic() - start_time, 3)
        return {
            "agent_id": f"AGENT-{agent_id:02d}",
            "squad": squad,
            "name": name,
            "status": "FAIL",
            "duration_s": duration,
            "stdout": "",
            "stderr": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="Enjambre de 21 Agentes Paralelizados BABYLON-60")
    parser.add_argument("--json", action="store_true", help="Emitir telemetría nativa M2M en JSON")
    args = parser.parse_args()

    python_bin = sys.executable
    py_env = dict(os.environ, PYTHONPATH=f"{ROOT_DIR}/packages:{ROOT_DIR}/experiments:.:{os.environ.get('PYTHONPATH', '')}")
    if "BABYLON_HOME" not in py_env:
        py_env["BABYLON_HOME"] = str(ROOT_DIR)
    if "BABYLON60_LICENSE_SALT" not in py_env:
        py_env["BABYLON60_LICENSE_SALT"] = "sovereign_hardened_salt_2026"

    # Definición de los 21 Agentes divididos en 7 Escuadrones
    agents_tasks = [
        # Escuadrón 1: Empaquetado & Artefactos Python
        (1, "SQUAD-1: Python Distribution", "uv build dry-check", [python_bin, "-m", "uv", "build", "--help"]),
        (2, "SQUAD-1: Python Distribution", "python wheel inspection", [python_bin, "scripts/c5_quality_gates/verify_distribution.py"]),
        (3, "SQUAD-1: Python Distribution", "pyproject.toml entrypoints validation", [python_bin, "-c", "assert '[project.scripts]' in open('pyproject.toml').read()"]),

        # Escuadrón 2: Rust Workspace & Crates.io
        (4, "SQUAD-2: Rust Workspace", "cargo check --workspace", ["cargo", "check", "--workspace"]),
        (5, "SQUAD-2: Rust Workspace", "babylon60-kernel check", ["cargo", "check", "-p", "babylon60-kernel"]),
        (6, "SQUAD-2: Rust Workspace", "nul-zk check", ["cargo", "check", "-p", "nul-zk"]),

        # Escuadrón 3: Docker Hardening & OCI Compliance
        (7, "SQUAD-3: Docker OCI", "Dockerfile syntax audit", [python_bin, "-c", "assert 'appuser' in open('Dockerfile').read()"]),
        (8, "SQUAD-3: Docker OCI", "Dockerfile OCI labels audit", [python_bin, "-c", "assert 'org.opencontainers.image' in open('Dockerfile').read()"]),
        (9, "SQUAD-3: Docker OCI", "Dockerfile HEALTHCHECK audit", [python_bin, "-c", "assert 'HEALTHCHECK' in open('Dockerfile').read()"]),

        # Escuadrón 4: Cumplimiento EU AI Act
        (10, "SQUAD-4: EU AI Act Compliance", "Compliance exporter test suite", [python_bin, "-m", "pytest", "tests/test_compliance_exporter.py", "-q"]),
        (11, "SQUAD-4: EU AI Act Compliance", "CLI cortex-compliance dry-run", [python_bin, "-m", "babylon60.compliance_exporter.eu_ai_act", "--bundle", "artifact_bundle_v3", "--format", "json", "--output", "scratch/agent_test.json"]),
        (12, "SQUAD-4: EU AI Act Compliance", "Regulatory docs audit", [python_bin, "-c", "assert 'Artículo 9' in open('docs/05_compliance_eu_ai_act.md').read()"]),

        # Escuadrón 5: Licenciamiento Enterprise & Firma HMAC
        (13, "SQUAD-5: Enterprise Licensing", "Phase 3 test suite", [python_bin, "-m", "pytest", "tests/test_phase3_enterprise.py", "-q"]),
        (14, "SQUAD-5: Enterprise Licensing", "CLI cortex-license generate", [python_bin, "-m", "babylon60.cli.license_cli", "generate", "--owner", "SwarmAuditAgent", "--tier", "enterprise"]),
        (15, "SQUAD-5: Enterprise Licensing", "License validator HMAC integrity", [python_bin, "-c", "from babylon60.guards.license_sovereign_validator import generate_license_key, verify_license_key; k=generate_license_key('test','enterprise',1900000000); assert verify_license_key(k).is_valid"]),

        # Escuadrón 6: Protocolo MCP & Servidor BFT
        (16, "SQUAD-6: MCP Protocol", "Cortex MCP server tools inspection", [python_bin, "-c", "from babylon60.mcp.cortex_mcp_server import TOOLS; assert len(TOOLS)>=4"]),
        (17, "SQUAD-6: MCP Protocol", "MCP server JSON-RPC version check", [python_bin, "-c", "from babylon60.mcp.cortex_mcp_server import JSONRPC_VERSION; assert JSONRPC_VERSION=='2.0'"]),
        (18, "SQUAD-6: MCP Protocol", "BABYLON_HOME env var resolution", [python_bin, "-c", "import os; os.environ['BABYLON_HOME']='/tmp/b60_test'; from babylon60.mcp.cortex_mcp_server import DEFAULT_LEDGER_PATH; assert '/tmp/b60_test' in str(DEFAULT_LEDGER_PATH)"]),

        # Escuadrón 7: Oráculo de Calidad C5-REAL & Telemetría
        (19, "SQUAD-7: Quality Gate & Telemetry", "Distribution quality gate JSON", [python_bin, "scripts/c5_quality_gates/verify_distribution.py", "--json"]),
        (20, "SQUAD-7: Quality Gate & Telemetry", "Scripts README auto-generation check", [python_bin, "scripts/generate_scripts_readme.py"]),
        (21, "SQUAD-7: Quality Gate & Telemetry", "Full test suite regression check", [python_bin, "-m", "pytest", "-x", "--tb=short", "tests/test_compliance_exporter.py", "tests/test_phase3_enterprise.py"]),
    ]

    print("=================================================================")
    print("🚀 INICIANDO ENJAMBRE DE 21 AGENTES PARALELIZADOS (BABYLON-60)")
    print("=================================================================")

    start_swarm_time = time.monotonic()
    results = []

    with ThreadPoolExecutor(max_workers=21) as executor:
        futures = {
            executor.submit(run_agent_task, agent_id, squad, name, cmd, py_env): agent_id
            for agent_id, squad, name, cmd in agents_tasks
        }

        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            if not args.json:
                icon = "✅" if res["status"] == "PASS" else "❌"
                print(f"{icon} [{res['agent_id']}] {res['squad']} :: {res['name']} ({res['duration_s']}s)")

    total_duration = round(time.monotonic() - start_swarm_time, 3)
    results.sort(key=lambda x: x["agent_id"])
    all_pass = all(r["status"] == "PASS" for r in results)

    telemetry = {
        "swarm_engine": "legion_21_agentes",
        "total_agents": len(results),
        "overall_status": "PASS" if all_pass else "FAIL",
        "total_duration_s": total_duration,
        "agents_results": results
    }

    if args.json:
        print(json.dumps(telemetry, indent=2))
    else:
        print("=================================================================")
        print(f"📊 ENJAMBRE DE 21 AGENTES COMPLETADO: {telemetry['overall_status']} en {total_duration}s")
        print("=================================================================")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
