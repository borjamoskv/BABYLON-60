#!/usr/bin/env python3
"""
BABYLON-60 Sovereign Launcher & Standalone Gateway (C5-REAL)
Author: Borja Fernández Angulo (borjamoskv)

Zero-dependency local HTTP server and browser bridge:
- Serves the BABYLON IDE UI (ui/index.html) with zero external packages (Pure Python Standard Library).
- Provides local REST telemetry (/api/status, /api/kernel/unbox, /api/ping).
- Auto-discovers free ports (default 6060 -> 6061 -> 6062...).
- Opens the system browser seamlessly in < 300 ms.
- Fallback safe: Never crashes; provides graceful degradation to file:// if binding fails.
"""

import os
import sys
import json
import math
import time
import socket
import signal
import platform
import threading
import subprocess as subprocess
import webbrowser
import urllib.parse
import re
import hashlib
import sqlite3
import shutil
from datetime import datetime, timezone
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Tuple, Optional, TYPE_CHECKING, Mapping
from types import FrameType
from socketserver import BaseServer

if TYPE_CHECKING:
    from scripts.lead_data_policy import MATRIX_CLASSIFICATION, CAMPAIGNS_DIR, open_synthetic_database
else:
    try:
        from scripts.lead_data_policy import MATRIX_CLASSIFICATION, CAMPAIGNS_DIR, open_synthetic_database
    except ModuleNotFoundError:
        from lead_data_policy import MATRIX_CLASSIFICATION, CAMPAIGNS_DIR, open_synthetic_database

REPO_ROOT = Path(__file__).resolve().parent.parent

UI_DIR = REPO_ROOT / "ui"
TARGET_KERNEL_DEBUG = REPO_ROOT / "target" / "debug" / "babylon60_kernel"
TARGET_KERNEL_RELEASE = REPO_ROOT / "target" / "release" / "babylon60_kernel"
CONFIG_FILE = Path.home() / ".babylon60_config.json"
MAX_SCENARIO_OPERATIONS = (1 << 53) - 1  # Exact integer range shared with JavaScript.
BIOMETRIC_DEMO_ACTION = "Demonstration: local biometric authorization"
BIOMETRIC_DEMO_SCOPE = "Demo only; not authorization for a production operation"
BIOMETRIC_DEMO_HASH = hashlib.sha256(b"BABYLON-60:biometric-demo:v1").hexdigest()
BENCH_ITERATIONS = 1_000_000
BENCH_TIMEOUT_SECONDS = 10
UNBOX_TIMEOUT_SECONDS = 5


def get_biometric_gate_path() -> Optional[Path]:
    custom_gate = Path.home() / ".local" / "bin" / "c5_biometric_gate"
    if custom_gate.exists() and os.access(custom_gate, os.X_OK):
        return custom_gate
    which_gate = shutil.which("c5_biometric_gate")
    if which_gate:
        return Path(which_gate)
    swift_gate = REPO_ROOT / "01_KISH_ENGINE" / "babylon60" / "guards" / "c5_biometric_gate.swift"
    if swift_gate.exists() and platform.system() == "Darwin":
        return swift_gate
    return None


def detect_installed_agents() -> dict[str, dict[str, str | bool]]:
    home = Path.home()
    return {
        "claude": {
            "name": "Claude Desktop / Code",
            "detected": any(
                p.exists()
                for p in [
                    Path("/Applications/Claude.app"),
                    home / "Applications/Claude.app",
                    home / "Library/Application Support/Claude",
                ]
            ),
            "description": "Protege herramientas MCP y ejecución de comandos.",
        },
        "cursor": {
            "name": "Cursor",
            "detected": any(
                p.exists()
                for p in [Path("/Applications/Cursor.app"), home / "Applications/Cursor.app", home / ".cursor"]
            ),
            "description": "Evita que el editor altere o borre repositorios sin huella.",
        },
        "vscode": {
            "name": "Visual Studio Code",
            "detected": any(
                p.exists()
                for p in [
                    Path("/Applications/Visual Studio Code.app"),
                    home / "Applications/Visual Studio Code.app",
                    home / ".vscode",
                ]
            ),
            "description": "Supervisa extensiones y agentes en VS Code.",
        },
        "antigravity": {
            "name": "Google Antigravity",
            "detected": (home / ".gemini/antigravity").exists(),
            "description": "Gobernanza de enjambres y subagentes autónomos.",
        },
        "terminal": {
            "name": "Terminal & Shell",
            "detected": True,
            "description": "Supervisión de scripts Python y comandos en segundo plano.",
        },
    }


def get_kernel_binary_path() -> Optional[Path]:
    if TARGET_KERNEL_RELEASE.exists() and os.access(TARGET_KERNEL_RELEASE, os.X_OK):
        return TARGET_KERNEL_RELEASE
    if TARGET_KERNEL_DEBUG.exists() and os.access(TARGET_KERNEL_DEBUG, os.X_OK):
        return TARGET_KERNEL_DEBUG
    return None


def check_touchid_available() -> bool:
    gate = get_biometric_gate_path()
    return gate is not None and platform.system() == "Darwin"


def parse_kernel_benchmark_output(output: str) -> Tuple[int, float, float]:
    """Parse one completed report, without treating incomplete output as a measurement."""
    counts = re.findall(r"\bCompleted\s+(\d+)\s+iterations\b", output)
    throughput = re.findall(r"\bThroughput:\s+(\S+)\s+Mops/sec\b", output)
    latency = re.findall(r"\bAverage Latency:\s+(\S+)\s+ns/op\b", output)
    if any(len(values) != 1 for values in (counts, throughput, latency)):
        raise ValueError("El ejecutable no devolvió un único informe completo de benchmark.")
    iterations, mops, ns = int(counts[0]), float(throughput[0]), float(latency[0])
    if iterations <= 0 or not all(math.isfinite(value) and value > 0 for value in (mops, ns)):
        raise ValueError("El benchmark devolvió iteraciones o métricas inválidas.")
    return iterations, mops, ns


def run_benchmark() -> Tuple[int, dict[str, object]]:
    kernel_path = get_kernel_binary_path()
    result: dict[str, object] = {
        "success": False,
        "iterations": None,
        "throughput_mops": None,
        "latency_ns": None,
        "mode": "Ring-0 Seqlock SPMC" if kernel_path else "Python Standalone",
        "raw_output": "",
        "measurement_source": "kernel" if kernel_path else "python_loop",
        "measured_at": None,
    }
    try:
        if kernel_path:
            process = subprocess.run(
                [str(kernel_path), "bench"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=BENCH_TIMEOUT_SECONDS,
            )
            result["raw_output"] = process.stdout or process.stderr
            if process.returncode != 0:
                raise ValueError(f"El benchmark nativo terminó con código {process.returncode}.")
            iterations, mops, ns = parse_kernel_benchmark_output(process.stdout)
        else:
            start = time.perf_counter()
            for _ in range(BENCH_ITERATIONS):
                pass
            elapsed = time.perf_counter() - start
            if not math.isfinite(elapsed) or elapsed <= 0:
                raise ValueError("No se obtuvo una duración válida para el bucle Python.")
            iterations = BENCH_ITERATIONS
            mops, ns = iterations / elapsed / 1_000_000, elapsed * 1_000_000_000 / iterations
            if not all(math.isfinite(value) and value > 0 for value in (mops, ns)):
                raise ValueError("No se obtuvieron métricas válidas para el bucle Python.")
            result["raw_output"] = f"Python loop: {iterations} iterations in {elapsed:.9f} seconds"
    except subprocess.TimeoutExpired:
        result["error"] = "Se agotó el plazo del benchmark nativo."
        return 504, result
    except Exception as error:
        result["error"] = str(error)
        return (502 if kernel_path else 500), result
    result.update(
        success=True,
        iterations=iterations,
        throughput_mops=mops,
        latency_ns=ns,
        measured_at=datetime.now(timezone.utc).isoformat(),
    )
    return 200, result


def run_unboxing() -> Tuple[int, dict[str, object]]:
    kernel_path = get_kernel_binary_path()
    script = REPO_ROOT / "scripts" / "c5_setup" / "unboxing_moskv1.py"
    source = "kernel" if kernel_path else "python_unboxing" if script.is_file() else None
    result = {
        "success": False,
        "output": "",
        "exit_code": None,
        "execution_source": source,
        "execution_scope": "COMMAND_EXECUTION_ONLY",
    }
    if source is None:
        result["error"] = "No hay ejecutable ni implementación Python de unboxing disponibles."
        return 503, result
    command = [str(kernel_path), "unbox"] if kernel_path else [sys.executable, str(script)]
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=UNBOX_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        result["error"] = "Se agotó el plazo de ejecución del comando."
        return 504, result
    except Exception as error:
        result["error"] = str(error)
        return 502, result
    result.update(output=process.stdout or process.stderr, exit_code=process.returncode)
    if process.returncode != 0:
        result["error"] = f"El comando terminó con código {process.returncode}."
        return 502, result
    result["success"] = True
    return 200, result


def get_telemetry_status() -> dict[str, object]:
    kernel_path = get_kernel_binary_path()
    has_kernel = kernel_path is not None
    cores = os.cpu_count() or 1
    arch = platform.machine()
    system = platform.system()
    has_touchid = check_touchid_available()

    return {
        "status": "ONLINE",
        "gateway_state": "ONLINE",
        "kernel_state": "BINARY_AVAILABLE" if has_kernel else "UNAVAILABLE",
        "timestamp": time.time(),
        "system": system,
        "architecture": arch,
        "hardware_threads": cores,
        "ring0_kernel_available": has_kernel,
        "kernel_binary_path": str(kernel_path) if kernel_path else None,
        "touchid_biometric_gate": has_touchid,
        "mode": "RING0_HYBRID" if has_kernel else "STANDALONE_LOCAL_FIRST",
        "cache_line_bytes": 64,
        "manifest_bytes": 64,
        "manifest_bytes_source": "architecture_specification",
        "exergy_target": 21000,
        "version": "60.4-SOVEREIGN",
    }


class BabylonHTTPHandler(SimpleHTTPRequestHandler):
    """Zero-dependency HTTP Handler serving the BABYLON-60 UI & Local APIs."""

    def __init__(self, request: socket.socket, client_address: tuple[str, int], server: BaseServer) -> None:
        super().__init__(request, client_address, server, directory=str(UI_DIR))

    def log_message(self, format: str, *args: object) -> None:
        # Silencia logs ruidosos de peticiones estáticas para mantener el terminal limpio
        try:
            msg = format % args if args else format
            if any(api in str(msg) for api in ["/api/", "500", "404", "error"]):
                super().log_message(format, *args)
        except Exception:
            pass

    def send_json(self, status: int, payload: Mapping[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        clean_path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query, keep_blank_values=True)

        # Rutas API
        if clean_path == "/api/status" or clean_path == "/api/ping":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            payload = get_telemetry_status()
            self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))
            return

        if clean_path == "/api/kernel/unbox":
            status, result = run_unboxing()
            self.send_json(status, result)
            return

        if clean_path == "/api/bench":
            status, result = run_benchmark()
            self.send_json(status, result)
            return

        if clean_path == "/api/leads/search":
            q = query_params.get("q", [""])[0].strip()
            sector = query_params.get("sector", [""])[0].strip()
            country = query_params.get("country", [""])[0].strip()
            try:
                limit = int(query_params.get("limit", [25])[0])
                if limit < 0:
                    raise ValueError("Negative result limit")
                limit = min(limit, 100)
            except ValueError:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "limit debe ser un entero >= 0."}).encode("utf-8"))
                return

            results = []
            total_matches = 0
            try:
                conn = open_synthetic_database()
            except (ValueError, sqlite3.Error):
                self.send_response(503)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"error": "Índice sintético inválido; reconstruye el índice."}).encode("utf-8")
                )
                return

            if conn is not None:
                c = conn.cursor()

                sql = "SELECT lead_id, company_name, domain, sector, city, country, target_role, contact_email, eu_ai_act_risk_classification, babylon60_pitch_vector FROM leads WHERE status = 'SYNTHETIC_ONLY'"
                params: list[str | int] = []

                if q:
                    sql += " AND (company_name LIKE ? OR domain LIKE ? OR contact_email LIKE ? OR sector LIKE ? OR target_role LIKE ?)"
                    params.extend([f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"])
                if sector:
                    sql += " AND sector LIKE ?"
                    params.append(f"%{sector}%")
                if country:
                    sql += " AND country LIKE ?"
                    params.append(f"%{country}%")

                count_sql = "SELECT COUNT(*) FROM (" + sql + ")"
                c.execute(count_sql, params)
                total_matches = c.fetchone()[0]

                sql += " LIMIT ?"
                params.append(limit)
                c.execute(sql, params)

                for row in c.fetchall():
                    results.append(
                        {
                            "lead_id": row[0],
                            "company_name": row[1],
                            "domain": row[2],
                            "sector": row[3],
                            "city": row[4],
                            "country": row[5],
                            "target_role": row[6],
                            "contact_email": row[7],
                            "risk_tier": row[8],
                            "pitch_vector": row[9],
                            "verification_status": "SYNTHETIC_ONLY · CONTACT UNVERIFIED",
                            "commercial_outreach_allowed": False,
                        }
                    )
                conn.close()

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "query": q,
                        "classification": MATRIX_CLASSIFICATION,
                        "index_status": "AVAILABLE" if conn is not None else "NOT_BUILT",
                        "commercial_outreach_allowed": False,
                        "total_matches": total_matches,
                        "returned_count": len(results),
                        "leads": results,
                    },
                    indent=2,
                ).encode("utf-8")
            )
            return

        if clean_path == "/api/compliance/pack":
            pack_path = REPO_ROOT / "compliance_reports" / "eu_ai_act_compliance_pack.json"
            pack_data = {}
            if pack_path.exists():
                with open(pack_path, "r", encoding="utf-8") as f:
                    pack_data = json.load(f)

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(pack_data, indent=2).encode("utf-8"))
            return

        if clean_path == "/api/guardrails/simulate":
            try:
                if any(len(query_params.get(key, [])) > 1 for key in ("n", "eps", "delta")):
                    raise ValueError("Scenario parameters must have exactly one value")
                n_text = query_params.get("n", ["10000000"])[0]
                if not re.fullmatch(r"[0-9]+", n_text):
                    raise ValueError("Operation count must be an integer written as digits")
                n = int(n_text)
                eps = float(query_params.get("eps", [0.01])[0])
                delta = float(query_params.get("delta", [0.001])[0])
                if not all(math.isfinite(value) for value in (eps, delta)):
                    raise ValueError("Non-finite scenario parameter")
                if not 0 <= n <= MAX_SCENARIO_OPERATIONS or not 0 <= eps <= 1 or not 0 <= delta <= 1:
                    raise ValueError("Scenario parameter outside its domain")
            except ValueError:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {
                            "error": f"Usa un único valor por parámetro: n debe ser un entero entre 0 y {MAX_SCENARIO_OPERATIONS}; eps y delta deben estar entre 0 y 1."
                        },
                        ensure_ascii=False,
                    ).encode("utf-8")
                )
                return

            # delta is P(control misses | model error), not an independent rate.
            prob_failure_per_call = eps * delta
            expected_joint_failures = n * prob_failure_per_call

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "transactions_annual": n,
                        "llm_error_rate_eps": eps,
                        "saas_guardrail_miss_rate_delta": delta,
                        "prob_failure_per_event": prob_failure_per_call,
                        "expected_joint_failures_annual": expected_joint_failures,
                        # Legacy aliases retained for clients; these are hypothetical inputs/results.
                        "expected_catastrophes_annual": round(expected_joint_failures, 2),
                        "saas_stack_failure_probability": "NO ESTIMADA: faltan datos del sistema evaluado.",
                        "babylon60_ring0_failure_probability": "NO ESTIMADA: faltan datos del sistema evaluado.",
                        "scenario_scope": (
                            "Escenario hipotético: eps = P(error); delta = P(omisión del control | error). "
                            "N × eps × delta estima fallos conjuntos esperados si esas tasas aplican a cada operación. "
                            "No mide catástrofes, brechas ni la probabilidad anual de fallo de un producto."
                        ),
                        "legal_liability_article_26": (
                            "Los proveedores y responsables del despliegue de sistemas de alto riesgo "
                            "tienen obligaciones propias (Arts. 16 y 26). El Art. 26 no atribuye toda responsabilidad al desplegador "
                            "ni exonera al proveedor."
                        ),
                        "sanctions_article_99": (
                            "Art. 99.3: hasta 35 M€ o el 7 % para infracciones del Art. 5. "
                            "Art. 99.4: hasta 15 M€ o el 3 % para las obligaciones enumeradas, "
                            "incluidas las de los Arts. 16 y 26. Los porcentajes se refieren al volumen "
                            "mundial del ejercicio anterior. Rige el límite mayor para empresas, "
                            "salvo pymes (menor, Art. 99.6) y pequeñas empresas de mediana "
                            "capitalización (menor para los apartados 4 y 5, Art. 99.6 bis). "
                            "La cuantía depende del caso."
                        ),
                        "due_diligence_verdict": "NO EVALUADA: el cálculo no determina cumplimiento ni responsabilidad jurídica.",
                        "legal_source": "https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng",
                    },
                    indent=2,
                ).encode("utf-8")
            )
            return

        if clean_path == "/api/gate/touchid":
            mode = query_params.get("mode", ["live"])[0].lower()
            if len(query_params.get("mode", [])) > 1 or mode not in ("live", "preview"):
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {"status": "INVALID_MODE", "error": "mode debe ser live o preview, con un único valor."}
                    ).encode("utf-8")
                )
                return
            gate_bin = Path("/Users/borjafernandezangulo/.local/bin/c5_biometric_gate")
            if not gate_bin.exists():
                gate_bin = REPO_ROOT / "01_KISH_ENGINE" / "babylon60" / "guards" / "c5_biometric_gate"

            if mode == "preview" or not gate_bin.exists():
                preview_txt = ""
                if gate_bin.exists():
                    try:
                        res = subprocess.run(
                            [
                                str(gate_bin),
                                "--preview",
                                "--action",
                                BIOMETRIC_DEMO_ACTION,
                                "--scope",
                                BIOMETRIC_DEMO_SCOPE,
                            ],
                            capture_output=True,
                            text=True,
                            timeout=5,
                        )
                        preview_txt = res.stdout
                    except Exception as e:
                        preview_txt = f"Preview error: {e}"
                else:
                    preview_txt = "c5_biometric_gate binary not compiled"

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(
                    json.dumps(
                        {
                            "status": "PREVIEW_OK",
                            "mode": "preview",
                            "authorization_scope": "DEMONSTRATION_ONLY",
                            "attestation_verified": False,
                            "preview_box": preview_txt,
                            "operator": "borjamoskv",
                            "attestation_type": "NIST P-256 Secure Enclave",
                        }
                    ).encode("utf-8")
                )
                return
            else:
                try:
                    res = subprocess.run(
                        [
                            str(gate_bin),
                            "--action",
                            BIOMETRIC_DEMO_ACTION,
                            "--scope",
                            BIOMETRIC_DEMO_SCOPE,
                            "--causal-hash",
                            BIOMETRIC_DEMO_HASH,
                        ],
                        capture_output=True,
                        text=True,
                        timeout=20,
                    )

                    stdout = res.stdout
                    # A successful process is a reported result, not verification of a signature.
                    authorization_reported = res.returncode == 0

                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps(
                            {
                                "status": "AUTHORIZATION_REPORTED" if authorization_reported else "FAILED",
                                "mode": "live_hardware",
                                "authorization_scope": "DEMONSTRATION_ONLY",
                                "attestation_verified": False,
                                "raw_output": stdout,
                                "exit_code": res.returncode,
                            }
                        ).encode("utf-8")
                    )
                    return
                except subprocess.TimeoutExpired:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(
                        json.dumps(
                            {"status": "TIMEOUT", "message": "Touch ID timeout: User did not tap the sensor within 20s"}
                        ).encode("utf-8")
                    )
                    return

        if clean_path == "/api/campaigns/dispatch":
            self.send_response(409)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "status": "BLOCKED_SYNTHETIC_DATA",
                        "error": "La matriz sintética no permite campañas ni despacho comercial.",
                    },
                    ensure_ascii=False,
                ).encode("utf-8")
            )
            return

        if clean_path == "/api/campaigns/merkle":
            manifest_file = CAMPAIGNS_DIR / "campaign_integrity_manifest.json"
            data = {}
            if manifest_file.exists():
                with open(manifest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))
            return

        if clean_path == "/api/campaigns/sectors":
            sectors_data = []
            try:
                conn = open_synthetic_database()
            except (ValueError, sqlite3.Error):
                self.send_response(503)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"error": "Índice sintético inválido; reconstruye el índice."}).encode("utf-8")
                )
                return
            if conn is not None:
                c = conn.cursor()
                c.execute(
                    "SELECT sector, COUNT(*) FROM leads WHERE status = 'SYNTHETIC_ONLY' GROUP BY sector ORDER BY COUNT(*) DESC"
                )
                counts = c.fetchall()
                total = sum(row[1] for row in counts)
                for row in counts:
                    sectors_data.append({"sector": row[0], "count": row[1], "pct": round(row[1] / total * 100, 2)})
                conn.close()

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "classification": MATRIX_CLASSIFICATION,
                        "commercial_outreach_allowed": False,
                        "total_sectors": len(sectors_data),
                        "sectors": sectors_data,
                    },
                    indent=2,
                ).encode("utf-8")
            )
            return

        if clean_path == "/api/dist/info":
            dist_dir = REPO_ROOT / "dist"
            packages = []
            if dist_dir.exists():
                for p in dist_dir.glob("*.zip"):
                    size_b = p.stat().st_size
                    packages.append(
                        {
                            "name": p.name,
                            "size_bytes": size_b,
                            "size_human": f"{round(size_b / 1024, 1)} KB",
                            "modified": p.stat().st_mtime,
                        }
                    )

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(
                json.dumps({"dist_dir": str(dist_dir), "packages": packages, "status": "READY"}, indent=2).encode(
                    "utf-8"
                )
            )
            return

        # Rutas de Asistente de Configuración (Setup Wizard)
        if clean_path == "/wizard" or clean_path == "/wizard.html":
            self.path = "/wizard.html"
            return super().do_GET()

        if clean_path == "/api/wizard/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            is_configured = CONFIG_FILE.exists()
            cfg_data = {}
            if is_configured:
                try:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                except Exception:
                    pass
            self.wfile.write(json.dumps({"configured": is_configured, "config": cfg_data}, indent=2).encode("utf-8"))
            return

        if clean_path == "/api/agents/detect":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            agents_info = detect_installed_agents()
            self.wfile.write(json.dumps(agents_info, indent=2).encode("utf-8"))
            return

        # Confinamiento estricto: denegar accesos con traversal o archivos ocultos
        if ".." in clean_path or clean_path.startswith("/."):
            self.send_error(403, "Acceso denegado: ruta restringida fuera de la frontera UI")
            return

        # Redirigir raíz al Asistente (si no está configurado) o al IDE
        if clean_path in ("/", "/index.html"):
            force_setup = "setup" in query_params or "wizard" in query_params
            if force_setup or not CONFIG_FILE.exists():
                self.path = "/wizard.html"
            else:
                self.path = "/index.html"
        elif clean_path == "/wizard":
            self.path = "/wizard.html"
        elif clean_path.startswith("/ui/"):
            # Mapear /ui/foo a /foo para servir directamente desde UI_DIR
            self.path = clean_path[3:]
        else:
            self.path = clean_path

        return super().do_GET()

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        clean_path = parsed_url.path

        if clean_path == "/api/wizard/complete":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            try:
                data = json.loads(body)
            except Exception:
                data = {}

            data["configured"] = True
            data["configured_at"] = time.time()
            write_success = True
            error_msg = ""
            try:
                CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                write_success = False
                error_msg = str(e)

            status_code = 200 if write_success else 500
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": write_success,
                "config": data if write_success else None,
                "error": error_msg if not write_success else None,
            }).encode("utf-8"))
            return

        if clean_path == "/api/create_app":
            create_app_sh = REPO_ROOT / "scripts" / "create_macos_app.sh"
            success = False
            output = ""
            if create_app_sh.exists():
                try:
                    res = subprocess.run(["bash", str(create_app_sh)], capture_output=True, text=True, timeout=15)
                    success = res.returncode == 0
                    output = res.stdout or res.stderr
                except Exception as e:
                    output = str(e)
            else:
                output = "Script create_macos_app.sh no encontrado."

            status_code = 200 if success else 500
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "output": output}).encode("utf-8"))
            return

        if clean_path == "/api/touchid/trigger":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            try:
                payload = json.loads(body)
            except Exception:
                payload = {}

            is_mock = payload.get("mock", False)
            gate = get_biometric_gate_path()

            if is_mock or not gate:
                # Estados excluyentes (P1-1): Demostración explícita sin hardware físico
                result = {
                    "success": True,
                    "status": "SIMULATED",
                    "mode": "DEMO_SIMULATION",
                    "verified_in_hardware": False,
                    "operator_user": os.getenv("USER", "operator"),
                    "causal_hash": "ce4aa229d47913d87b321c81ef9326e5e9b8f2c253457d451296bf3cb492d063",
                    "signature": "DEMO-SIMULATED-NO-HARDWARE-P256",
                    "message": "Demostración de flujo: sensor biométrico no activado / simulado",
                    "timestamp": time.time(),
                }
            else:
                try:
                    # Import the installed package or its checkout source. No trust-on-first-use.
                    package_root = str(REPO_ROOT / "01_KISH_ENGINE")
                    if package_root not in sys.path:
                        sys.path.insert(0, package_root)
                    from babylon60.verification.hardware_attestation import (
                        configured_public_key, request_attestation, verify_attestation,
                    )
                    import secrets

                    trusted_key = configured_public_key()
                    challenge = json.dumps({"purpose": "local-biometric-check", "version": 1,
                                            "nonce": secrets.token_hex(32)}, sort_keys=True).encode()
                    evidence = request_attestation(challenge, gate, "Verify local biometric challenge",
                                                   "Local gateway; no transaction is executed", trusted_key)
                    verified = verify_attestation(challenge, evidence, trusted_key)
                    result = {
                        "success": True,
                        "status": "ATTESTED",
                        "mode": "HARDWARE_TOUCH_ID",
                        "verified_in_hardware": True,
                        "operator_user": verified.get("operator_user"),
                        "causal_hash": verified["causal_hash"],
                        "signature": verified["secure_enclave_signature"],
                        "timestamp": time.time(),
                    }
                except subprocess.TimeoutExpired:
                    result = {
                        "success": False,
                        "status": "TIMEOUT",
                        "mode": "HARDWARE_TOUCH_ID",
                        "verified_in_hardware": False,
                        "error": "Tiempo de espera de autorización Touch ID agotado (25s)",
                    }
                except Exception as e:
                    result = {
                        "success": False,
                        "status": "ERROR",
                        "mode": "HARDWARE_TOUCH_ID",
                        "verified_in_hardware": False,
                        "error": str(e),
                    }

            self.send_response(200 if result.get("success") else 400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def find_available_port(start_port: int = 6060, max_attempts: int = 20) -> int:
    """Busca un puerto libre de forma no bloqueante."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


class BabylonHTTPServer(HTTPServer):
    """HTTPServer sin reverse-DNS (evita bloqueo de 5s en socket.getfqdn sobre VMs macOS CI)."""

    allow_reuse_address = True

    def server_bind(self) -> None:
        socket.socket.setsockopt(self.socket, socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.server_address = self.socket.getsockname()
        host, port = self.server_address[:2]
        self.server_name = str(host)
        self.server_port = int(port)


def run_server(port: int = 6060, open_browser: bool = True) -> None:
    actual_port = find_available_port(port)
    server_address = ("127.0.0.1", actual_port)

    try:
        httpd = BabylonHTTPServer(server_address, BabylonHTTPHandler)
    except Exception as e:
        print(f"[!] No se pudo bindear el servidor HTTP en el puerto {actual_port}: {e}")
        fallback_file = UI_DIR / "index.html"
        print(f"[*] Conmutando a fallback directo: {fallback_file}")
        if open_browser and fallback_file.exists():
            webbrowser.open(f"file://{fallback_file.resolve()}")
        sys.exit(0)

    url = f"http://localhost:{actual_port}/"
    wizard_url = f"{url}wizard"
    print("============================================================")
    print("      BABYLON IDE — Gateway Soberano de 1-Clic")
    print("      Hypervisor: MOSKV-1 | Zero-Friction Engine")
    print("============================================================")
    print(f"  > URL LOCAL:         {url}")
    print(f"  > ASISTENTE 1-CLIC:  {wizard_url}")
    print("  > INTERFAZ GRÁFICA:  ui/index.html")
    print(f"  > TELEMETRÍA API:    {url}api/status")
    print(f"  > MODO OPERATIVO:    {get_telemetry_status()['mode']}")
    print("============================================================\n")

    if open_browser:

        def launch_browser() -> None:
            time.sleep(0.3)
            print(f"[*] Abriendo navegador del sistema en {url} ...")
            webbrowser.open(url)

        t = threading.Thread(target=launch_browser, daemon=True)
        t.start()

    def signal_handler(sig: int, frame: FrameType | None) -> None:
        print("\n[*] Deteniendo Gateway Soberano de BABYLON-60...")
        httpd.server_close()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        httpd.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        httpd.server_close()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="BABYLON-60 Launcher & Standalone Bridge")
    parser.add_argument("--port", type=int, default=6060, help="Puerto de escucha (default 6060)")
    parser.add_argument("--no-browser", action="store_true", help="No abrir automáticamente el navegador")
    parser.add_argument("--check-only", action="store_true", help="Comprobar entorno, emitir JSON y salir con 0")
    parser.add_argument("--test-port", action="store_true", help="Verificar enlace a puerto y salir")

    args = parser.parse_args()

    if args.check_only:
        status = get_telemetry_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)

    if args.test_port:
        port = find_available_port(args.port)
        print(f"PORT_AVAILABLE:{port}")
        sys.exit(0)

    run_server(port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
