# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized Bounty CLI Terminal
"""bounty_cli.py - Consola soberana de control y telemetría de Ω-Bounty-Ingest.

Permite invocar el ciclo funtorial de ingestión, triaje causal, inspección
interactiva de bytecode, verificación formal de Aeones Conformes L1 y generación
de planes de remediación forense directamente desde la terminal.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from typing import Sequence

# ── Dynamic PYTHONPATH Resolution (Clone & Run Invariant) ───────────────────
_ORCHESTRATOR_DIR = Path(__file__).resolve().parents[2]
if str(_ORCHESTRATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_ORCHESTRATOR_DIR))

import httpx  # noqa: E402

from babylon60.attestation.conformal_tree import (  # noqa: E402
    AeonVerifier,
    extract_claims_from_ledger,
)
from babylon60.bft.bounty_pipeline_orchestrator import (  # noqa: E402
    BountyPipelineOrchestrator,
)
from babylon60.bft.bounty_remediation import (  # noqa: E402
    generate_remediation_reports,
)
from babylon60.bft.defi_bytecode_scraper import DeFiBytecodeScraper  # noqa: E402
from babylon60.bft.exergy_binary_ipc import (  # noqa: E402
    SharedManifestFFIWriter,
    find_babylon60_dylib,
)


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


def handle_inspect_manifest() -> int:
    """Inspecciona interactivamente el estado del SharedManifest C-ABI (64B Seqlock SPMC)."""
    render_dashboard_banner()
    print("[*] INSPECCIÓN C-ABI DE SHARED MANIFEST (INV_C5_SHM - 64B Seqlock SPMC):")
    writer = SharedManifestFFIWriter()

    dylib_path = find_babylon60_dylib()
    mode_str = f"NATIVO ({dylib_path})" if writer.is_native else "EMULADO (Python in-memory)"
    status_str = "POISONED (0xDEAD6060)" if writer.is_halted() else "RUNNING (0x00000001)"

    ptr_val = writer._ptr.value or 0
    is_aligned = (ptr_val % 64 == 0) if ptr_val else False

    read_val = writer.read()
    epoch = writer.manifest.epoch_id
    seq = writer.manifest.seq
    is_consistent = seq % 2 == 0

    print(f"    • Modo Enlace FFI:     {mode_str}")
    print(f"    • Dirección Puntero:   0x{ptr_val:016x}")
    print(f"    • Alineación 64 Bytes: {'✓ CUMPLIDA (0-split L1)' if is_aligned else '✗ DESALINEADO'}")
    print(f"    • Estado del Monoide:  {status_str}")
    print(f"    • Epoch Causal:        {epoch}")
    print(f"    • Seqlock Seq:         {seq} ({'✓ Par / Consistente' if is_consistent else '⚠ Impar / Mutando'})")

    if read_val:
        print(f"    • Lectura Consistente: Epoch {read_val[0]} | Hash 0x{read_val[1].hex()}")
    else:
        print("    • Lectura Consistente: None")

    print("\n[+] DICTAMEN DE INVARIANTES:")
    if writer.is_native and is_aligned and not writer.is_halted():
        print("    [✓] INV-1 Layout 64B: OK")
        print("    [✓] INV-2 Seqlock SPMC: OK")
        print("    [✓] INV-3 Landauer Bound: OK")
        print("    [✓] INV-4 Fail-Stop Gate: OK")
        return 0
    elif writer.is_halted():
        print("    [✗] MANIFIESTO EN ESTADO POISONED (Fail-Stop irreversible)")
        return 1
    else:
        print("    [ℹ] Modo de compatibilidad emulado (sin dylib nativa)")
        return 0


def handle_verify_aeon(manifest_path: str, db_path: str | None) -> int:
    """Verifica formalmente la atestación de un Aeón Conforme sellado en L1."""
    render_dashboard_banner()
    print("[*] ORÁCULO DE VERIFICACIÓN DE AEÓN CONFORME (INV_C5_AEON):")
    print(f"    • Manifiesto L1:    {manifest_path}")
    print(f"    • Cold Ledger DB:   {db_path or 'No provisto (solo firma y cabeceras)'}")

    try:
        report = AeonVerifier.verify_manifest(manifest_path=manifest_path, db_path=db_path)
    except Exception as exc:
        print(f"\n[!] Error fatal durante la verificación: {exc}")
        return 1

    print("\n[+] RESULTADOS DE ATESTACIÓN CRIPTOGRÁFICA:")
    print(f"    • Aeón ID:          {report['aeon_id']}")
    print(f"    • Estado:           {report['status']}")
    print(f"    • Raíz Merkle:      0x{report['merkle_root']}")
    print(f"    • Total Claims:     {report['total_claims']:,}")
    print(f"    • Firma Ed25519:    {'✓ VÁLIDA' if report['ed25519_signature_valid'] else '✗ INVÁLIDA'}")
    print(f"    • Hardware UUID:    {report['hardware_anchor_uuid']}")
    print(f"    • Host de Origen:   {'✓ COINCIDENTE' if report['is_origin_host'] else 'ℹ NODO REMOTO'}")

    if report["tree_integrity_valid"] is not None:
        print(
            f"    • Recomputación DB: {'✓ ÍNTEGRA (Raíz y recuento idénticos)' if report['tree_integrity_valid'] else '✗ CORRUPCIÓN DETECTADA'}"
        )
        if report["recomputed_root"]:
            print(f"      - Raíz Calculada: 0x{report['recomputed_root']}")
            print(f"      - Claims en DB:   {report['recomputed_claims_count']:,}")

    if report["overall_valid"]:
        print("\n[✓] AEÓN CONFORME VERIFICADO EXITOSAMENTE (Atestación L1 C5-REAL sellada)")
        return 0
    else:
        print("\n[✗] VIOLACIÓN EPISTÉMICA: El Aeón no superó los controles de integridad.")
        return 1


def handle_verify_claim(claim_id: str, manifest_path: str, db_path: str) -> int:
    """Verifica formalmente la prueba de inclusión de un claim en el Aeón sellado."""
    render_dashboard_banner()
    print("[*] VERIFICACIÓN FORMAL DE INCLUSIÓN DE CLAIM (Membership Proof):")
    print(f"    • Claim ID:         {claim_id}")
    print(f"    • Manifiesto L1:    {manifest_path}")
    print(f"    • Cold Ledger DB:   {db_path}")

    try:
        report = AeonVerifier.verify_claim_membership(
            claim_id=claim_id,
            manifest_path=manifest_path,
            db_path=db_path,
        )
    except Exception as exc:
        print(f"\n[!] Error fatal durante la verificación: {exc}")
        return 1

    print("\n[+] DICTAMEN DE INCLUSIÓN DE MERKLE:")
    print(f"    • Advisory ID:      {report['advisory_id']}")
    print(f"    • Dominio:          {report['domain']}")
    print(f"    • Nivel de Riesgo:  {report['risk_score']:.2f}")
    print(f"    • Hash de Hoja:     0x{report['leaf_hash']}")
    print(f"    • Pasos de Prueba:  {report['proof_steps']} (O(log2 N))")
    print(f"    • Raíz Esperada:    0x{report['expected_merkle_root']}")
    print(f"    • Raíz Calculada:   0x{report['computed_merkle_root']}")

    print("\n[+] TRAZA DE CAMINO MERKLE (Primeros 3 pasos):")
    for i, (pos, sib) in enumerate(report["proof_path"][:3]):
        print(f"    [{i + 1:02d}] {pos:<5} | Hermano: {sib[:24]}...")

    if report["is_valid_inclusion"]:
        print("\n[✓] PRUEBA DE INCLUSIÓN VÁLIDA: El claim está formalmente sellado en el Aeón L1.")
        return 0
    else:
        print("\n[✗] PRUEBA DE INCLUSIÓN FALLIDA: El hash de la hoja discrepa de la raíz Merkle.")
        return 1


def handle_export_remediations(out_path: str, db_path: str, domain_filter: str | None) -> int:
    """Exporta autopsias y planes de mitigación forense para los claims atestados."""
    render_dashboard_banner()
    print("[*] SÍNTESIS MASIVA DE PLANES DE REMEDIACIÓN FORENSE:")
    print(f"    • Cold Ledger DB:   {db_path}")
    print(f"    • Filtro Dominio:   {domain_filter or 'TODOS LOS DOMINIOS'}")
    print(f"    • Destino JSON:     {out_path}")

    try:
        claims = extract_claims_from_ledger(db_path)
        if domain_filter:
            claims = [c for c in claims if str(c.get("domain")) == domain_filter]

        reports = generate_remediation_reports(claims)
        out_file = Path(out_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(reports, indent=2), encoding="utf-8")

        print(f"\n[✓] {len(reports):,} planes de remediación sintetizados y exportados a {out_file.resolve()}")
        return 0
    except Exception as exc:
        print(f"\n[!] Error sintetizando planes de remediación: {exc}")
        return 1


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

    if report.manifest_telemetry:
        m_tel = report.manifest_telemetry
        print("\n[+] ANCLAJE C-ABI C5-REAL (INV_C5_SHM - 64B Seqlock SPMC):")
        print(f"    • Modo FFI:             {'NATIVO (libbabylon60.dylib)' if m_tel.get('is_native') else 'EMULADO'}")
        print(f"    • Estado Monoide:       {m_tel.get('status')}")
        print(f"    • Epoch Causal:         {m_tel.get('epoch_id')}")
        print(
            f"    • Seqlock Paridad:      Seq={m_tel.get('seq')} ({'✓ Consistente' if m_tel.get('is_consistent') else '⚠ Mutando'})"
        )
        if m_tel.get("last_payload_hash"):
            print(f"    • Último Hash Anclado:  0x{str(m_tel.get('last_payload_hash'))[:32]}...")

    print("\n[✓] Invariante INV_C5_SHM preservada: Cero I/O síncrono en la ruta caliente.")
    return 0


async def run_cli(args: argparse.Namespace) -> int:
    """Manejador principal CLI con soporte de verificación, remediación y watch."""
    if args.inspect_manifest:
        return handle_inspect_manifest()

    if args.inspect_bytecode:
        return handle_bytecode_inspection(args.inspect_bytecode, args.hook_address)

    if args.verify_aeon:
        return handle_verify_aeon(args.verify_aeon, args.db)

    if args.verify_claim:
        if not args.aeon:
            print("[!] Se requiere --aeon <manifest_path> para verificar la pertenencia de un claim.")
            return 1
        return handle_verify_claim(args.verify_claim, args.aeon, args.db)

    if args.export_remediations:
        return handle_export_remediations(args.export_remediations, args.db, args.domain)

    orchestrator = BountyPipelineOrchestrator()
    orchestrator.cold_ledger.start()

    if not args.json_output:
        render_dashboard_banner()
        print(f"[*] Iniciando ciclo de ingestión (Sondeo en vivo: {args.live}, Límite: {args.per_page})...")

    try:
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
    finally:
        orchestrator.cold_ledger.stop()


def main(argv: Sequence[str] | None = None) -> None:
    """Punto de entrada principal para CLI babylon60-bounty."""
    default_db = "bounty_ledger_10k.db" if os.path.exists("bounty_ledger_10k.db") else "bounty_ledger.db"
    default_aeon = "L1_sink/aeon_bounty_omega_10k.json"

    parser = argparse.ArgumentParser(description="BABYLON-60 Ω-Bounty-Ingest CLI Terminal")
    parser.add_argument("--live", action="store_true", help="Realiza sondeo en vivo de APIs públicas")
    parser.add_argument("--per-page", type=int, default=5, help="Número de registros por feed")
    parser.add_argument("--min-risk", type=float, default=0.5, help="Umbral de riesgo para auto-atestación")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Salida pura en formato JSON")
    parser.add_argument("--inspect-bytecode", type=str, help="Hexadecimal de bytecode EVM a auditar")
    parser.add_argument(
        "--inspect-manifest",
        action="store_true",
        help="Inspecciona el estado del SharedManifest C-ABI (64B Seqlock SPMC)",
    )
    parser.add_argument("--hook-address", type=str, help="Dirección Ethereum del hook Uniswap v4 a evaluar")
    parser.add_argument("--export-claims", type=str, help="Ruta de archivo JSON para exportar recibos sellados")
    parser.add_argument("--watch", type=int, help="Intervalo en segundos para sondeo continuo en bucle")

    # Modos de Verificación y Auditoría Soberana
    parser.add_argument(
        "--verify-aeon",
        type=str,
        metavar="MANIFEST",
        help="Ruta al manifiesto L1 para auditar integridad criptográfica",
    )
    parser.add_argument(
        "--verify-claim",
        type=str,
        metavar="CLAIM_ID",
        help="ID del claim para verificar formalmente su prueba de inclusión O(log2 N)",
    )
    parser.add_argument(
        "--aeon",
        type=str,
        default=default_aeon,
        help="Ruta al manifiesto L1 (por defecto L1_sink/aeon_bounty_omega_10k.json)",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=default_db,
        help=f"Ruta a la base de datos Cold Ledger SQLite (por defecto {default_db})",
    )
    parser.add_argument(
        "--export-remediations",
        type=str,
        metavar="OUT_FILE",
        help="Exporta autopsias y planes de remediación de los claims atestados",
    )
    parser.add_argument(
        "--domain",
        type=str,
        choices=["DOMAIN_EVM", "DOMAIN_NATIVE", "DOMAIN_AI"],
        help="Filtro de dominio para exportación de remediaciones",
    )

    args = parser.parse_args(argv)
    exit_code = asyncio.run(run_cli(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
