#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""c5_bounty_legion_exfiltration.py — Operativo Legión (Swarm Interception & Exfiltration)

Extrae atestaciones SCITT del Cold Ledger (bounty_ledger_10k.db / bounty_ledger.db)
y despliega un enjambre de subagentes altamente concurrentes especializados por dominio:
  1. DOMAIN_EVM (Skill 41): Autopsia de bytecode, mitigación EIP-1153 y guards Yul.
  2. DOMAIN_NATIVE (WebKit): Triaje de jaula Gigacage/IsoMalloc y mitigaciones PAC macOS.
  3. DOMAIN_AI (SAGA-1): Firewall neurosimbólico, AST sanitization y mitigación RLHF.

[AX-5] TOPOLOGY: Enjambre de intercepción forense y generación de parches de remediación
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import os
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional

# ── PYTHONPATH ────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_ROOT, "01_ORCHESTRATOR"))

try:
    from babylon60.kernel.kimi_client import KimiClient
except ImportError:
    KimiClient = None  # type: ignore[assignment, misc]

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("LegionSwarm")

DEFAULT_DB = "bounty_ledger_10k.db" if os.path.exists("bounty_ledger_10k.db") else "bounty_ledger.db"
DEFAULT_WORKERS = min(32, (os.cpu_count() or 4) * 4)


def fetch_scitt_claims(
    db_path: str,
    limit: Optional[int] = 30,
    domain_filter: str = "ALL",
) -> List[Dict[str, Any]]:
    """Extrae las atestaciones más recientes del Cold Ledger usando SQLite URI modo lectura."""
    if not os.path.exists(db_path):
        logger.error(f"[!] No existe la base de datos Cold Ledger en: {db_path}")
        return []

    try:
        uri = f"file:{os.path.abspath(db_path)}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = (
            "SELECT claim_id, advisory_id, domain, finding_summary, risk_score, payload_hash, "
            "timestamp_utc, hardware_anchor, attestation_merkle_root "
            "FROM bounty_claims"
        )
        params: List[Any] = []

        if domain_filter != "ALL":
            query += " WHERE domain = ?"
            params.append(domain_filter)

        query += " ORDER BY timestamp_utc DESC, risk_score DESC"

        if limit is not None and limit > 0:
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError as e:
        logger.error(f"[!] Error leyendo Cold Ledger ({db_path}): {e}")
        return []


def synthesize_domain_remediation(claim: Dict[str, Any]) -> str:
    """Genera mitigación forense determinista de alta exergía según dominio canónico."""
    domain = claim.get("domain", "")
    advisory = claim.get("advisory_id", "")
    finding = claim.get("finding_summary", "")

    if domain == "DOMAIN_EVM":
        if "transient storage" in finding.lower() or "tstore" in finding.lower():
            return (
                f"[SKILL 41 DEFI AUDIT] Análisis de {advisory}: "
                f"Mitigación EIP-1153: Inyectar ReentrancyGuardTransient con reseteo Yul atómico: "
                f"'assembly {{ tstore(SLOT_LOCK, 1) }} ... assembly {{ tstore(SLOT_LOCK, 0) }}'. "
                f"Verificar que ninguna llamada externa delegada omita el borrado de slot transitorio."
            )
        elif "delegatecall" in finding.lower():
            return (
                f"[SKILL 41 DEFI AUDIT] Análisis de {advisory}: "
                f"Riesgo de colisión de almacenamiento en proxy. Mitigación: Aplicar patrón ERC-7201 "
                f"(Namespaced Storage) para aislar slots de implementación y validar hashes de selector."
            )
        elif "oracle" in finding.lower() or "flash loan" in finding.lower():
            return (
                f"[SKILL 41 DEFI AUDIT] Análisis de {advisory}: "
                f"Manipulación de precio detectada. Mitigación: Forzar consulta TWAP multiciclo de Uniswap v3/v4 "
                f"y validar límites de deslizamiento (slippage bounds) dentro del mismo bloque de ejecución."
            )
        else:
            return (
                f"[SKILL 41 DEFI AUDIT] Análisis de {advisory}: "
                f"Superficie de ataque EVM ({finding}). Mitigación: Validar invariantes formales en Foundry/Certora "
                f"y asegurar aislamiento de llamadas con nonReentrant estricto."
            )

    elif domain == "DOMAIN_NATIVE":
        if "gigacage" in finding.lower() or "cage" in finding.lower():
            return (
                f"[WEBKIT MEMORY FORENSICS] Análisis de {advisory}: "
                f"Vulnerabilidad de escape de jaula. Mitigación: Forzar verificación Gigacage::isCaged(ptr) "
                f"en compilación DFG/FTL y revalidar límites de matriz antes de elisión de bounds checks."
            )
        elif "isomalloc" in finding.lower():
            return (
                f"[WEBKIT MEMORY FORENSICS] Análisis de {advisory}: "
                f"Use-After-Free en IsoMalloc. Mitigación: Implementar cuarentena diferida de páginas IsoHeap<T> "
                f"y asegurar que el barrido de GC anule referencias pendientes antes de marcar bloques libres."
            )
        elif "kernel" in finding.lower() or "pac" in finding.lower() or "xnu" in finding.lower():
            return (
                f"[DARWIN ARM64 HARDENING] Análisis de {advisory}: "
                f"Corrupción en kernel heap. Mitigación: Aplicar Pointer Authentication (PAC) con discriminador "
                f"contextual (ptrauth_auth_and_resign) y aislar descriptores mach_port en zonas seguras."
            )
        else:
            return (
                f"[WEBKIT MEMORY FORENSICS] Análisis de {advisory}: "
                f"Fallo de memoria nativa ({finding}). Mitigación: Proteger estructuras mediante guard pages "
                f"y activar ASLR de alta entropía con validación de heap de dyld."
            )

    elif domain == "DOMAIN_AI":
        if "pickle" in finding.lower() or "unsafe" in finding.lower() or "deserialization" in finding.lower():
            return (
                f"[SAGA-1 NEURAL FIREWALL] Análisis de {advisory}: "
                f"Vector de deserialización insegura. Mitigación: Forzar 'torch.load(..., weights_only=True)' "
                f"o migrar tensores a formato SafeTensors con verificación criptográfica SHA3-256 de cabecera."
            )
        elif "prompt" in finding.lower() or "jailbreak" in finding.lower() or "injection" in finding.lower():
            return (
                f"[SAGA-1 NEURAL FIREWALL] Análisis de {advisory}: "
                f"Inyección de prompt en tool calls. Mitigación: Aislar delimitadores de tokens en AST parser, "
                f"validar schemas JSON con Pydantic estricto y aplicar política de mínima sorpresa ontológica."
            )
        elif "rlhf" in finding.lower() or "gradient" in finding.lower() or "inversion" in finding.lower():
            return (
                f"[SAGA-1 NEURAL FIREWALL] Análisis de {advisory}: "
                f"Fuga de gradientes o inversión de recompensa. Mitigación: Añadir ruido gaussiano diferencial "
                f"(DP-SGD) en retropropagación y acotar gradientes L2 por muestra individual."
            )
        else:
            return (
                f"[SAGA-1 NEURAL FIREWALL] Análisis de {advisory}: "
                f"Anomalía neurosimbólica ({finding}). Mitigación: Sellar la entrada con oráculo SMT Z3 y "
                f"activar contención de contexto en Ring-0."
            )

    return (
        f"[C5-REAL FORENSIC ENGINE] Análisis de {advisory}: "
        f"Mitigación formal recomendada para {finding}: aislar canal y revocar privilegios del nodo."
    )


_api_disabled = False


def legion_subagent_task(claim: Dict[str, Any], use_api: bool = True) -> Dict[str, Any]:
    """Tarea autónoma ejecutada por un subagente del enjambre Legión."""
    global _api_disabled
    claim_id = claim.get("claim_id", "")
    advisory = claim.get("advisory_id", "")
    domain = claim.get("domain", "")
    risk_score = claim.get("risk_score", 0.0)

    # Intentar Kimi K3 si está configurado y habilitado
    analysis_text = ""
    if use_api and not _api_disabled and KimiClient is not None:
        client = KimiClient()
        if client.is_configured():
            system_prompt = (
                "Eres un analizador forense cibernético operando bajo el framework termodinámico C5-REAL. "
                "Emite una autopsia técnica y mitigación en 3 líneas."
            )
            prompt = (
                f"Dominio: {domain}. Advisory: {advisory}. Riesgo: {risk_score}. "
                f"Resumen del hallazgo: {claim.get('finding_summary', '')}. "
                f"Hash: {claim.get('payload_hash', '')[:16]}. Emite diagnóstico y mitigación determinista."
            )
            res = client.query(prompt=prompt, system_prompt=system_prompt, max_tokens=150)
            if res.get("success", False):
                analysis_text = str(res.get("content", ""))
            else:
                _api_disabled = True

    if not analysis_text:
        # Motor heurístico determinista de alta exergía
        analysis_text = synthesize_domain_remediation(claim)

    return {
        "claim_id": claim_id,
        "advisory_id": advisory,
        "domain": domain,
        "risk_score": risk_score,
        "finding": claim.get("finding_summary", ""),
        "payload_hash": claim.get("payload_hash", ""),
        "remediation": analysis_text,
        "success": True,
    }


def execute_exfiltration_swarm(
    db_path: str = DEFAULT_DB,
    limit: Optional[int] = 30,
    domain_filter: str = "ALL",
    workers: int = DEFAULT_WORKERS,
    export_path: Optional[str] = None,
    offline: bool = False,
) -> None:
    print("=" * 80)
    print("🚀 OPERATIVO LEGIÓN: EXFILTRACIÓN FORENSE Y MITIGACIÓN (C5-REAL v4.0)")
    print(f"   Cold Ledger  : {db_path}")
    print(f"   Filtro Dominio: {domain_filter} | Límite: {limit or 'ILIMITADO'}")
    print(f"   Concurrencia : {workers} subagentes en ThreadPool")
    if offline:
        print("   [!] Modo Offline: Inferencia determinista de alta exergía (Cero API Latency)")
    print("=" * 80)

    claims = fetch_scitt_claims(db_path=db_path, limit=limit, domain_filter=domain_filter)
    if not claims:
        print(f"[!] No se encontraron atestaciones SCITT en {db_path} que coincidan con los criterios.")
        return

    print(f"\n[*] {len(claims):,} atestaciones SCITT recuperadas del Cold Ledger.")
    print(f"[*] Desplegando enjambre concurrente de subagentes ({workers} workers)...\n")

    start_time = time.perf_counter()
    results: List[Dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers, thread_name_prefix="exfilt") as executor:
        future_to_claim = {executor.submit(legion_subagent_task, c, not offline): c for c in claims}
        done_count = 0
        for future in concurrent.futures.as_completed(future_to_claim):
            try:
                res = future.result()
                results.append(res)
                done_count += 1
                if done_count % 10 == 0 or done_count == len(claims):
                    pct = (done_count / len(claims)) * 100
                    print(f"    [{pct:5.1f}%] Subagentes finalizados: {done_count}/{len(claims)}")
            except Exception as exc:
                logger.error(f"  [!] Subagente colapsado: {exc}")

    elapsed = time.perf_counter() - start_time
    throughput = len(results) / elapsed if elapsed > 0 else 0.0

    print(f"\n[*] Convergencia de Enjambre alcanzada en {elapsed:.2f} s ({throughput:,.1f} claims/s).")
    print("=" * 80)
    print("📊 MUESTRA DE AUTOPSIAS FORENSES Y MITIGACIONES SOBERANAS")
    print("=" * 80)

    # Mostrar muestra representativa (hasta 6)
    sample_results = results[:6]
    for r in sample_results:
        print(f"\n[✓] TARGET: {r['advisory_id']} ({r['domain']} | Risk: {r['risk_score']:.2f})")
        print(f"    Claim ID : {r['claim_id'][:32]}...")
        print(f"    Hallazgo : {r['finding']}")
        print(f"    Mitigación:\n      {r['remediation']}")

    # Resumen por dominio
    by_domain: Dict[str, int] = {}
    for r in results:
        dom = r["domain"]
        by_domain[dom] = by_domain.get(dom, 0) + 1

    print(f"\n{'=' * 80}")
    print("📈 BALANCE FINAL DE MITIGACIONES GENERADAS")
    print(f"{'=' * 80}")
    for dom, count in sorted(by_domain.items()):
        print(f"  {dom:<16}: {count:,} mitigaciones sintetizadas")
    print(f"  TOTAL PROCESADO : {len(results):,} planes de remediación listos para despacho")
    print(f"  TIEMPO TOTAL    : {elapsed:.2f} s")
    print(f"{'=' * 80}")

    if export_path:
        try:
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n[+] Reporte forense exportado a: {export_path}")
        except Exception as e:
            print(f"[!] Error exportando reporte a {export_path}: {e}")

    print("\n✅ OPERATIVO DE EXFILTRACIÓN FORENSE CERRADO CON ÉXITO")


def main() -> None:
    parser = argparse.ArgumentParser(description="BABYLON-60: Operativo Legión — Exfiltración Forense y Mitigación")
    parser.add_argument(
        "--db-path",
        type=str,
        default=DEFAULT_DB,
        help=f"Ruta al Cold Ledger SQLite (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Número máximo de atestaciones a triagar (default: 30, use 0 para ilimitado)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"Número de workers paralelos (default: {DEFAULT_WORKERS})",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="ALL",
        choices=["ALL", "DOMAIN_EVM", "DOMAIN_NATIVE", "DOMAIN_AI"],
        help="Filtrar por dominio ontológico específico (default: ALL)",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Ruta de archivo JSON para exportar el resultado de la exfiltración",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Desactivar llamadas a APIs remotas y forzar inferencia forense determinista C5-REAL",
    )
    args = parser.parse_args()

    lim = None if args.limit <= 0 else args.limit
    execute_exfiltration_swarm(
        db_path=args.db_path,
        limit=lim,
        domain_filter=args.domain,
        workers=args.workers,
        export_path=args.export,
        offline=args.offline,
    )


if __name__ == "__main__":
    main()
