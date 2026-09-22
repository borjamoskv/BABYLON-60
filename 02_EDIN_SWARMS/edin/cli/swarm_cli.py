#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ EDIN & SHARUR-3600 SVEREIGN SWARM CLI | DOMAIN: edin.swarms | C5-REAL
# ============================================================================
"""
Sovereign CLI for EDIN Swarm Operations:
  - SHARUR-3600 Sexagesimal Mass Parallel Sweeps
  - KUDURRU-64 Gravity Filter & Anti-Cognitive DDoS Verification
  - Apple Silicon Unified Memory & Mac Studio Ultra 256GB Profiler
  - Fuzzy Topology Intent Routing (SwarmRouter)
"""

import argparse
import ast
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from edin.swarms import (
    SharurSwarmTopology,
    SexagesimalScale,
    KudurruGravityFilter,
)
from edin import (
    UnifiedMemoryProfiler,
    SwarmRouter,
    AttestationEnvelope,
)

# Extensiones de archivo auditadas por defecto
AUDIT_EXTENSIONS = {".py", ".rs", ".b60", ".lean", ".sh", ".toml"}
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", "target", "dist", "build", ".cortex"}


def _audit_file_worker(filepath: str, agent_id: int) -> dict:
    """Función de trabajo síncrona para auditoría AST y comprobación de integridad."""
    rel = os.path.basename(filepath)
    violations = []
    ast_ok = True

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return {
            "file": rel,
            "agent_id": agent_id,
            "ast_ok": False,
            "violations": [f"Read error: {e}"],
        }

    if filepath.endswith(".py"):
        try:
            ast.parse(content, filename=filepath)
        except SyntaxError as e:
            ast_ok = False
            violations.append(f"AST SyntaxError L{e.lineno}: {e.msg}")

    # Búsqueda de anergía: except crudo sin log
    if "except:" in content:
        violations.append("Raw swallowed exception handler")

    return {
        "file": rel,
        "agent_id": agent_id,
        "ast_ok": ast_ok,
        "violations": violations,
    }


def cmd_sweep(args: argparse.Namespace) -> int:
    """Ejecuta barrido paralelo con SHARUR-3600."""
    target_dir = Path(args.target).expanduser().resolve()
    if not target_dir.exists():
        print(f"[-] Error: Target directory '{target_dir}' does not exist.", file=sys.stderr)
        return 1

    scale_map = {
        "soss": SexagesimalScale.SOSS,
        "ner": SexagesimalScale.NER,
        "sar": SexagesimalScale.SAR,
        "sar_u": SexagesimalScale.SAR_U,
    }
    scale = scale_map.get(args.scale.lower(), SexagesimalScale.SAR)

    # Recolección de archivos
    files: List[str] = []
    for root, dirs, filenames in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in filenames:
            if any(f.endswith(ext) for ext in AUDIT_EXTENSIONS):
                files.append(os.path.join(root, f))

    files.sort()
    total_files = len(files)

    print("=" * 70)
    print(" 🦅 BABYLON-60 | SHARUR-3600 SEXAGESIMAL PARALLEL SWARM AUDITOR")
    print("=" * 70)
    print(f"[*] Directorio Objetivo : {target_dir}")
    print(f"[*] Escala Sexagesimal  : {scale.name} ({int(scale)} subagentes virtuales)")
    print(f"[*] Núcleos de Proceso  : {args.workers}")
    print(f"[*] Archivos a Auditar  : {total_files}\n")

    if total_files == 0:
        print("[!] No se encontraron archivos fuente compatibles para auditar.")
        return 0

    sharur = SharurSwarmTopology(scale=scale, process_workers=args.workers)
    summary = sharur.execute_parallel_cpu_sweep(files, _audit_file_worker)

    print("--- RESULTADOS DEL BARRIDO ---")
    print(f"  Archivos Procesados   : {summary.total_items}")
    print(f"  Archivos Limpios (OK) : {summary.passed_items}")
    print(f"  Archivos con Fricción : {summary.failed_items}")
    print(f"  Rendimiento de Barrido: {summary.items_per_second:.1f} archivos/segundo")
    print(f"  Tiempo Total de Muro  : {summary.telemetry.wall_time_s:.3f} s")
    print(f"  Involuntary CS (ru)   : {summary.telemetry.involuntary_cs} (Anti-Thrashing)")
    print(f"  Voluntary CS (ru)     : {summary.telemetry.voluntary_cs}")
    print(f"  Max RSS Memoria       : {summary.telemetry.max_rss_mb:.1f} MB")

    if args.output:
        out_path = Path(args.output).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        report_data = {
            "target": str(target_dir),
            "scale": scale.name,
            "workers": int(scale),
            "total_items": summary.total_items,
            "passed_items": summary.passed_items,
            "failed_items": summary.failed_items,
            "items_per_second": summary.items_per_second,
            "telemetry": summary.telemetry.to_dict(),
            "results": summary.results,
        }
        out_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        print(f"\n[+] Informe persistido en: {out_path}")

    print("=" * 70)
    return 0 if summary.failed_items == 0 else 2


def cmd_profile(args: argparse.Namespace) -> int:
    """Perfilador de hardware de silicio y memoria unificada."""
    profiler = UnifiedMemoryProfiler(override_ram_gb=args.override_ram)
    report = profiler.get_hardware_report()

    print("=" * 70)
    print(" ⚡ BABYLON-60 | UNIFIED MEMORY & SILICON HARDWARE PROFILER")
    print("=" * 70)
    print(f"  Sistema Operativo     : {report.os_system} ({report.architecture})")
    print(f"  Apple Silicon Nativo  : {'SÍ (ARM64)' if report.is_apple_silicon else 'NO'}")
    print(f"  Clase Mac Studio Ultra: {'SÍ (>= 120GB)' if report.is_ultra_class else 'NO'}")
    print(f"  RAM Física Unificada  : {report.total_ram_gb:.1f} GB")
    print(f"  RAM Disponible Seguro : {report.available_ram_gb:.1f} GB (80% buffer)")
    print(f"  Backend Recomendado   : {report.recommended_backend}")
    print(f"  Límite Parámetros Q4  : {report.max_hostable_params_q4_billions:.1f}B parámetros sin swap")
    print(f"  Swap Risk Score       : {report.swap_risk_score:.2f} (Zero-Thrashing Target)")

    if args.simulate_ultra:
        print("\n--- SIMULACIÓN HOJA DE RUTA: MAC STUDIO ULTRA 256GB ---")
        sim = profiler.simulate_mac_studio_ultra_256gb()
        for p in sim["projections"]:
            fit_mark = "✓ AJUSTA" if p["fits_zero_swap"] else "✗ DESBORDA"
            print(
                f"  [{fit_mark}] {p['model']:<34} Pesos: {p['weights_gb']:>5.1f} GB | Total: {p['total_ram_gb']:>5.1f} GB | Agentes: {p['max_swarm_agents']}"
            )

    print("=" * 70)
    return 0


def cmd_kudurru(args: argparse.Namespace) -> int:
    """Evalúa un candidato a través de la membrana KUDURRU-64."""
    kudurru = KudurruGravityFilter(min_exergy=args.min_exergy, auto_init_ring0=True)

    envelope = AttestationEnvelope.create(
        sender_id=args.sender,
        recipient_id="ring0_shared_manifest",
        payload={"data": args.payload, "notes": "Submitted via edin-swarm CLI"},
    )

    res = kudurru.evaluate_and_promote(envelope, candidate_exergy=args.exergy)

    print("=" * 70)
    print(" 🛡️  KUDURRU-64 | MEMBRANA GRAVITACIONAL & VERIFICADOR DE EXERGÍA")
    print("=" * 70)
    print(f"  Aceptado para Ring-0  : {'SÍ' if res.accepted else 'NO'}")
    print(f"  Descarte Silencioso   : {'SÍ (Silent Drop)' if res.silent_drop else 'NO'}")
    print(f"  Puntuación de Exergía : {res.exergy_score:.3f} (Umbral: {args.min_exergy:.3f})")
    print(f"  Razón / Diagnóstico   : {res.reason}")
    if res.digest_hex:
        print(f"  SHA3-256 Digest       : {res.digest_hex}")
    if res.promoted_to_ring0:
        print(f"  Commit Seqlock Ring-0 : PUBLICADO (Epoch {res.epoch})")
    print("=" * 70)

    return 0 if res.accepted else 1


def cmd_route(args: argparse.Namespace) -> int:
    """Enruta una intención en lenguaje natural a la topología adecuada."""
    target, conf = SwarmRouter.route_query(args.intent)
    print("=" * 70)
    print(" 🧭 SWARM ROUTER | DESPACHADOR DE TOPOLOGÍAS TOLERANTE A TYPOS")
    print("=" * 70)
    print(f'  Intención Evaluada    : "{args.intent}"')
    print(f"  Topología Asignada    : {target.value}")
    print(f"  Confianza de Matching : {conf * 100:.1f}%")
    print("=" * 70)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="babylon60-swarm",
        description="BABYLON-60 Sovereign Swarm & EDIN Orchestration CLI (C5-REAL)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # sweep
    p_sweep = subparsers.add_parser("sweep", help="Barrido masivo paralelo con SHARUR-3600")
    p_sweep.add_argument("--target", "-t", default=".", help="Directorio objetivo a auditar")
    p_sweep.add_argument(
        "--scale",
        "-s",
        default="sar",
        choices=["soss", "ner", "sar", "sar_u"],
        help="Escala sexagesimal (60, 600, 3600, 36000)",
    )
    p_sweep.add_argument("--workers", "-w", type=int, default=10, help="Número de procesos paralelos (P-cores)")
    p_sweep.add_argument("--output", "-o", default=None, help="Ruta de salida JSON para el informe")

    # profile
    p_prof = subparsers.add_parser("profile", help="Perfilado de hardware de silicio y memoria unificada")
    p_prof.add_argument("--override-ram", type=float, default=None, help="Simular cantidad de RAM en GB")
    p_prof.add_argument(
        "--simulate-ultra", action="store_true", default=True, help="Mostrar proyección Mac Studio Ultra 256GB"
    )

    # kudurru
    p_kud = subparsers.add_parser("kudurru", help="Prueba de criba en membrana KUDURRU-64")
    p_kud.add_argument("--payload", "-p", required=True, help="Texto o carga útil de prueba")
    p_kud.add_argument("--exergy", "-e", type=float, default=0.85, help="Puntuación de exergía candidata [0.0 - 1.0]")
    p_kud.add_argument("--min-exergy", type=float, default=0.618, help="Umbral mínimo de exergía de la membrana")
    p_kud.add_argument("--sender", default="sharur_agent_cli", help="ID del subagente emisor")

    # route
    p_route = subparsers.add_parser("route", help="Enrutamiento tolerante a fallos de intenciones")
    p_route.add_argument("intent", help="Texto de intención del usuario (ej: 'enjmabres')")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "sweep":
        return cmd_sweep(args)
    elif args.command == "profile":
        return cmd_profile(args)
    elif args.command == "kudurru":
        return cmd_kudurru(args)
    elif args.command == "route":
        return cmd_route(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
