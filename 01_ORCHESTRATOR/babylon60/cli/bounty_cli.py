# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized Bounty CLI Terminal
"""bounty_cli.py - Consola soberana de control y telemetría de Ω-Bounty-Ingest.

Permite invocar el ciclo funtorial de ingestión, triaje causal, inspección
interactiva de bytecode y anclaje de reclamaciones criptográficas desde la terminal.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys
from typing import Sequence

import httpx

from babylon60.bft.bounty_pipeline_orchestrator import BountyPipelineOrchestrator
from babylon60.bft.defi_bytecode_scraper import DeFiBytecodeScraper


def render_dashboard_banner() -> None:
    """Renderiza la cabecera canónica Industrial Noir 2026."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════╗
║  BABYLON-60 v4.1 | Ω-BOUNTY-INGEST COGNITIVE PIPELINE                   ║
║  STATE: C5-REAL  | HARDWARE ANCHOR: DARWIN ARM64 | TOPOLOGY: ZERO-IO     ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def handle_bytecode_inspection(bytecode_hex: str, hook_addr: str | None) -> int:
    """Inspecciona interactivamente un fragmento de bytecode EVM desde la terminal."""
    render_dashboard_banner()
    print("[*] INSPECCIÓN CUANTITATIVA DE BYTECODE EVM (Skill 41):")
    scraper = DeFiBytecodeScraper()
    res = scraper.analyze_bytecode(bytecode_hex, address=hook_addr)

    print(f"    • Dirección Hook:     {res.contract_address or 'No provista'}")
    print(f"    • Puntuación Riesgo:  {res.risk_score:.2f}")
    print(f"    • Opcodes TSTORE:     {res.tstore_count} (0x5d)")
    print(f"    • Opcodes TLOAD:      {res.tload_count} (0x5e)")
    print(f"    • DELEGATECALL:       {res.delegatecall_count} (0xf4)")
    print(f"    • SELFDESTRUCT:       {res.selfdestruct_count} (0xff)")
    print(f"    • ORIGIN:             {res.origin_count} (0x32)")
    print(f"    • CREATE2:            {res.create2_count} (0xf5)")

    if res.hook_permissions and res.hook_permissions.raw_bits > 0:
        print(f"    • Máscara Permisos:   0x{res.hook_permissions.raw_bits:04x}")
        print(f"      - before_swap:      {res.hook_permissions.before_swap}")
        print(f"      - after_swap:       {res.hook_permissions.after_swap}")
        print(f"      - returns_delta:    {res.hook_permissions.before_swap_returns_delta}")

    print("\n[+] DICTAMEN DE INVARIANTES:")
    for f in res.findings:
        print(f"    [!] {f}")

    return 0


async def run_single_cycle(args: argparse.Namespace, orchestrator: BountyPipelineOrchestrator) -> int:
    """Ejecuta una ronda de ingestión y triaje."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        report = await orchestrator.execute_cycle(
            client=client if args.live else None,
            per_page=args.per_page,
            auto_attest_high_risk=True,
            risk_threshold=args.min_risk,
        )

    if args.json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return 0

    print("\n[+] TELEMETRÍA DE CICLO FUNTORIAL:")
    print(f"    • Timestamp UTC:        {report.timestamp_utc}")
    print(f"    • Tramas B60IPC:        {report.frames_ingested}")
    print(f"    • Latencia Total:       {report.total_elapsed_ms:.2f} ms")
    print(f"    • Cota de Landauer:     {report.landauer_dissipated_joules:.2e} Joules")
    print(f"    • Profundidad Previa:   {report.queue_depths_pre_drain}")

    print("\n[+] RESULTADOS POR ESPECIALISTAS:")
    print(f"    • EVM (Uniswap/Hooks):  {len(report.evm_analyses)} analizados")
    for evm in report.evm_analyses:
        print(f"      - Target: {evm.contract_address} | Risk: {evm.risk_score:.2f} | Findings: {evm.findings}")

    print(f"    • Nativo (WebKit/JSC):  {len(report.native_triages)} analizados")
    for nat in report.native_triages:
        print(
            f"      - Advisory: {nat.advisory_id} | Class: {nat.vulnerability_class} | Subsystems: {nat.affected_subsystems}"
        )

    print(f"    • AI (SAGA-1 Sentinel): {len(report.ai_sentinel_dicta)} analizados")
    for ai in report.ai_sentinel_dicta:
        print(f"      - Advisory: {ai.advisory_id} | Threat: {ai.vulnerability_class.value} | Taint: {ai.taint_level}")

    print(f"\n[+] RECIBOS DE RECLAMACIÓN SELLADOS (Proof of Claim): {len(report.claim_receipts)}")
    for rcpt in report.claim_receipts:
        print(f"    • [{rcpt.domain}] {rcpt.claim_id}")
        print(f"      - Merkle Root:     {rcpt.attestation_merkle_root}")
        print(f"      - Hardware Anchor: {rcpt.hardware_anchor}")
        print(f"      - Payload Hash:    {rcpt.payload_hash[:16]}...")

    if args.export_claims and report.claim_receipts:
        export_path = Path(args.export_claims)
        export_path.write_text(json.dumps([r.to_dict() for r in report.claim_receipts], indent=2), encoding="utf-8")
        print(f"\n[✓] Recibos exportados a {export_path.resolve()}")

    print("\n[✓] Invariante INV_C5_SHM preservada: Cero I/O síncrono en la ruta caliente.")
    orchestrator.cold_ledger.stop()
    return 0


async def run_cli(args: argparse.Namespace) -> int:
    """Manejador principal CLI con soporte de modo watch y dry-run."""
    if args.inspect_bytecode:
        return handle_bytecode_inspection(args.inspect_bytecode, args.hook_address)

    orchestrator = BountyPipelineOrchestrator()

    if not args.json_output:
        render_dashboard_banner()
        print(f"[*] Iniciando ciclo de ingestión (Sondeo en vivo: {args.live}, Límite: {args.per_page})...")

    if args.watch and args.watch > 0:
        print(f"[*] Modo vigilancia activo (Intervalo: {args.watch}s). Presiona Ctrl+C para detener.")
        try:
            while True:
                await run_single_cycle(args, orchestrator)
                await asyncio.sleep(args.watch)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n[!] Vigilancia interrumpida por el operador. Transición limpia a halt.")
            return 0

    return await run_single_cycle(args, orchestrator)


def main(argv: Sequence[str] | None = None) -> None:
    """Punto de entrada principal para CLI babylon60-bounty."""
    parser = argparse.ArgumentParser(description="BABYLON-60 Ω-Bounty-Ingest CLI Terminal")
    parser.add_argument("--live", action="store_true", help="Realiza sondeo en vivo de APIs públicas")
    parser.add_argument("--per-page", type=int, default=5, help="Número de registros por feed")
    parser.add_argument("--min-risk", type=float, default=0.5, help="Umbral de riesgo para auto-atestación")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Salida pura en formato JSON")
    parser.add_argument("--inspect-bytecode", type=str, help="Hexadecimal de bytecode EVM a auditar")
    parser.add_argument("--hook-address", type=str, help="Dirección Ethereum del hook Uniswap v4 a evaluar")
    parser.add_argument("--export-claims", type=str, help="Ruta de archivo JSON para exportar recibos sellados")
    parser.add_argument("--watch", type=int, help="Intervalo en segundos para sondeo continuo en bucle")

    args = parser.parse_args(argv)
    exit_code = asyncio.run(run_cli(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
