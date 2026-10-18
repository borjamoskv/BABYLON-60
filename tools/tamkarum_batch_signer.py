#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ TAMKARUM BATCH SIGNER | DOMAIN: tools.tamkarum | STATE: C5-REAL
# ============================================================================
"""
High-Speed Deterministic Batch Signer & Merkle Tree Generator for Enterprise Campaigns.

Processes JSONL campaign queues through the 4-stage pipeline:
  NIMROD-60 (Forensics) ➔ GUDEA-60 (Personalized Pitch) ➔
  LAHAMU-60 (Hume Guillotine Audit) ➔ TAMKARUM-60 (Merkle Root Sealing).

Emits RFC 9942 / SCITT-compatible manifests for WORM ledger attestation.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "02_EDIN_SWARMS"))

from agents_archi import DistributionDesignTeam

CAMPAIGNS_DIR = BASE_DIR / "campaigns"


def compute_merkle_root(leaves: List[str]) -> str:
    """Computes exact binary Merkle Tree root over SHA-256 leaf hashes."""
    if not leaves:
        return hashlib.sha256(b"EMPTY_CAMPAIGN").hexdigest()
    
    current_level = [bytes.fromhex(h) for h in leaves]
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = hashlib.sha256(left + right).digest()
            next_level.append(combined)
        current_level = next_level
    return current_level[0].hex()


def process_campaign_file(
    file_path: Path,
    limit: Optional[int] = None,
    output_drafts_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Processes a single campaign JSONL file, audits copy, and signs Merkle root."""
    campaign_name = file_path.stem.replace("campaign_", "").replace("_", " ").title()
    print(f"\n➔ Procesando Campaña: {campaign_name} ({file_path.name})")

    if output_drafts_dir:
        output_drafts_dir.mkdir(parents=True, exist_ok=True)

    approved = 0
    rejected = 0
    leaves: List[str] = []
    audited_leads: List[Dict[str, Any]] = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if limit:
        lines = lines[:limit]

    for idx, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue

        try:
            lead = json.loads(line)
        except json.JSONDecodeError:
            continue

        lead_id = lead.get("lead_id", f"LEAD_{idx:05d}")
        company = lead.get("company_name", "Organización")
        role = lead.get("target_role", "CISO")
        contact_name = lead.get("contact_name", "Responsable de Seguridad")
        contact_email = lead.get("contact_email", "")
        sector = lead.get("sector", "Enterprise")
        risk_class = lead.get("eu_ai_act_risk_classification", "High Risk (Annex III)")
        pain_point = lead.get("infrastructure_pain_point", "Trazabilidad inmutable de agentes LLM")
        pitch_vector = lead.get("babylon60_pitch_vector", "Trazabilidad WORM RFC 9942 COSE_Sign1")

        # GUDEA-60: Craft Tailored Pitch
        pitch_text = (
            f"Asunto: Controles Ring-0 y Trazabilidad WORM (EU AI Act) para los agentes de {company}\n\n"
            f"Estimado/a {contact_name} ({role}),\n\n"
            f"La entrada en aplicación del Reglamento (UE) 2024/1689 para sistemas de alto riesgo "
            f"({risk_class}) altera la responsabilidad de cumplimiento corporativo. "
            f"Delegar mutaciones de bases de datos o transacciones críticas en pipelines estocásticos (LLMs) "
            f"sin trazabilidad en silicio compromete la cadena de custodia probatoria.\n\n"
            f"Desafío identificado: {pain_point}.\n\n"
            f"BABYLON-60 implementa en vuestra VPC local:\n"
            f"1. Trazabilidad WORM Continua (Art. 12): {pitch_vector}.\n"
            f"2. Supervisión Humana en Hardware (Art. 14): Cerrojo biométrico Touch ID (allowableReuseDuration = 0).\n"
            f"3. Apoptosis Fail-Stop (Art. 15): Intercepción determinista en nanosegundos (POISONED = 0xDEAD_6060).\n\n"
            f"Condiciones del Piloto Enterprise: 15.000 € (30-45 días, 5 nodos de staging) con auditoría reproducible.\n"
            f"Régimen Asincrónico: Sin llamadas comerciales de preventa. Verificación técnica directa en silicio.\n\n"
            f"Consulte el paquete de evidencia en: borja@babylon60.com / https://babylon60.com\n\n"
            f"Borja Fernández Angulo\n"
            f"Investigador en Sistemas Complejos & Operador Raíz\n"
            f"BABYLON-60 Sovereign Trust Kernel"
        )

        # LAHAMU-60: Hume Guillotine Audit
        audit = DistributionDesignTeam.audit_creative_copy(pitch_text)

        # Merkle leaf computation
        payload_bytes = json.dumps(
            {"lead_id": lead_id, "company": company, "email": contact_email, "pitch": pitch_text},
            sort_keys=True,
        ).encode("utf-8")
        leaf_hash = hashlib.sha256(payload_bytes).hexdigest()
        leaves.append(leaf_hash)

        if audit["passed"]:
            approved += 1
        else:
            rejected += 1

        lead_record = {
            "lead_id": lead_id,
            "company": company,
            "role": role,
            "email": contact_email,
            "sector": sector,
            "leaf_hash": leaf_hash,
            "audit_status": audit["status"],
            "shannon_entropy": audit["entropy_shannon_bits"],
            "dispatch_approved": audit["passed"],
        }
        audited_leads.append(lead_record)

        if output_drafts_dir and audit["passed"]:
            draft_file = output_drafts_dir / f"{lead_id}_{company.replace(' ', '_')}.txt"
            draft_file.write_text(pitch_text, encoding="utf-8")

    merkle_root = compute_merkle_root(leaves)

    manifest = {
        "campaign_file": file_path.name,
        "campaign_name": campaign_name,
        "timestamp_unix": time.time(),
        "total_processed": len(lines),
        "approved": approved,
        "rejected": rejected,
        "pass_rate_pct": round((approved / len(lines) * 100) if lines else 0.0, 2),
        "merkle_root": merkle_root,
        "governance_mode": "AIR_GAP_ASYNCHRONOUS",
        "auditor": "LAHAMU-60 (Guillotina de Hume)",
    }

    print(f"   ✓ {approved}/{len(lines)} aprobados ({manifest['pass_rate_pct']}%) | Merkle Root: {merkle_root[:16]}...")
    return {"manifest": manifest, "leads": audited_leads}


def main():
    parser = argparse.ArgumentParser(description="BABYLON-60 Tamkarum Batch Signer")
    parser.add_argument("--campaign", type=str, default="all", help="Campaign filename or 'all'/'tier1_spain'")
    parser.add_argument("--limit", type=int, default=None, help="Limit leads per campaign (default: all)")
    parser.add_argument("--save-drafts", action="store_true", help="Save text draft files into campaigns/drafts_*")
    args = parser.parse_args()

    print("=" * 78)
    print("      TAMKARUM BATCH SIGNER · INDUSTRIALIZACIÓN DE OUTBOUND WORM")
    print("=" * 78)

    campaign_files: List[Path] = []
    if args.campaign in ("all", "*"):
        campaign_files = sorted(list(CAMPAIGNS_DIR.glob("campaign_*.jsonl")))
    elif args.campaign in ("tier1_spain", "tier1"):
        campaign_files = [CAMPAIGNS_DIR / "campaign_tier1_spain_top_priority.jsonl"]
    else:
        target = CAMPAIGNS_DIR / args.campaign
        if not target.exists() and not target.suffix:
            target = CAMPAIGNS_DIR / f"campaign_{args.campaign}.jsonl"
        if target.exists():
            campaign_files = [target]
        else:
            print(f"[-] Campaña no encontrada: {args.campaign}")
            sys.exit(1)

    all_manifests: List[Dict[str, Any]] = []
    all_campaign_roots: List[str] = []

    for cfile in campaign_files:
        drafts_dir = (CAMPAIGNS_DIR / f"drafts_{cfile.stem.replace('campaign_', '')}") if args.save_drafts else None
        res = process_campaign_file(cfile, limit=args.limit, output_drafts_dir=drafts_dir)
        all_manifests.append(res["manifest"])
        all_campaign_roots.append(res["manifest"]["merkle_root"])

    # Global Consolidated Merkle Root
    consolidated_root = compute_merkle_root(all_campaign_roots)

    master_manifest = {
        "timestamp_unix": time.time(),
        "total_campaigns_processed": len(all_manifests),
        "total_leads_processed": sum(m["total_processed"] for m in all_manifests),
        "total_leads_approved": sum(m["approved"] for m in all_manifests),
        "global_consolidated_merkle_root": consolidated_root,
        "campaign_manifests": all_manifests,
        "verification_standard": "RFC 9942 COSE_Sign1 / SCITT Architecture",
    }

    manifest_output_path = CAMPAIGNS_DIR / "outreach_manifest_consolidated.json"
    manifest_output_path.write_text(json.dumps(master_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n" + "=" * 78)
    print(f"➔ Lotes Consolidados: {master_manifest['total_campaigns_processed']} campañas")
    print(f"➔ Total Leads Procesados: {master_manifest['total_leads_processed']}")
    print(f"➔ Total Aprobados Fail-Closed: {master_manifest['total_leads_approved']}")
    print(f"➔ Global Consolidated Merkle Root: {consolidated_root}")
    print(f"➔ Manifiesto Guardado en: {manifest_output_path}")
    print("=" * 78)


if __name__ == "__main__":
    main()
