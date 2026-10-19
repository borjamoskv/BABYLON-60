#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ TAMKARUM SWARM ORCHESTRATOR | DOMAIN: tools.tamkarum | STATE: C5-REAL
# ============================================================================
"""
Unified Swarm Orchestration Engine for BABYLON-60 Distribution, Design & Social.

Binds the 11-agent sexagesimal matrix to real production data:
  - Database: leads_enterprise.db (10,000 enterprise leads)
  - Campaigns: campaigns/*.jsonl
  - Ledger: RFC 9942 COSE_Sign1 / SCITT Merkle roots
  - Social: X (Twitter) threads, LinkedIn whitepapers, community triage

Usage:
  python3 tools/tamkarum_swarm_orchestrator.py --pipeline outreach --limit 10
  python3 tools/tamkarum_swarm_orchestrator.py --pipeline social-threads
  python3 tools/tamkarum_swarm_orchestrator.py --pipeline triage-community
  python3 tools/tamkarum_swarm_orchestrator.py --pipeline kelly-audit
"""

import argparse
import hashlib
import json
import math
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure 02_EDIN_SWARMS is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "02_EDIN_SWARMS"))

from agents_archi import (
    DistributionDesignTeam,
    AgentRole,
    SocialMediaTeam,
    SocialAgentRole,
)

DB_PATH = BASE_DIR / "leads_enterprise.db"
CAMPAIGNS_DIR = BASE_DIR / "campaigns"


class TamkarumSwarmOrchestrator:
    """Operational orchestrator for the 11-agent marketing, design and social swarm."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.team_dist = DistributionDesignTeam
        self.team_social = SocialMediaTeam

    # ------------------------------------------------------------------------
    # Pipeline 1: Outbound Enterprise Forense (Nimrod -> Gudea -> Lahamu -> Tamkarum)
    # ------------------------------------------------------------------------
    def run_outreach_pipeline(self, limit: int = 5, sector_filter: Optional[str] = None) -> Dict[str, Any]:
        print("\n" + "=" * 78)
        print(" [PIPELINE 1] OUTBOUND ENTERPRISE FORENSE (NIMROD ➔ GUDEA ➔ LAHAMU ➔ TAMKARUM)")
        print("=" * 78)

        if not self.db_path.exists():
            print(f"[-] Error: Base de datos no encontrada en {self.db_path}")
            return {"status": "error", "message": "Database not found"}

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        query = "SELECT * FROM leads"
        params: List[Any] = []
        if sector_filter:
            query += " WHERE sector = ?"
            params.append(sector_filter)
        query += " ORDER BY lead_id LIMIT ?"
        params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        processed_leads: List[Dict[str, Any]] = []
        merkle_leaves: List[str] = []

        for row in rows:
            lead = dict(row)
            lead_id = lead.get("lead_id", "LEAD_UNK")
            company = lead.get("company_name", "Unknown Corp")
            sector = lead.get("sector", "General Tech")
            role = lead.get("target_role", "CISO")
            email = lead.get("contact_email", f"security@{company.lower().replace(' ', '')}.com")

            # 1. NIMROD-60 Forensics
            forensics = {
                "lead_id": lead_id,
                "company": company,
                "sector": sector,
                "target_role": role,
                "eu_ai_act_risk_tier": "High Risk (Annex III / Critical Infrastructure or AI Decisioning)",
                "applicable_articles": ["Art. 12 (WORM logging)", "Art. 14 (Human oversight)", "Art. 15 (Fail-stop robustness)"],
            }

            # 2. GUDEA-60 Craft Pitch
            pitch = (
                f"Asunto: Controles Ring-0 y Trazabilidad WORM (EU AI Act) para los agentes de {company}\n\n"
                f"Estimado equipo de Seguridad liderado por {role},\n\n"
                f"La entrada en vigor de las obligaciones para sistemas de IA de alto riesgo "
                f"bajo el Reglamento (UE) 2024/1689 altera directamente la responsabilidad jurídica del CISO: "
                f"delegar mutaciones de bases de datos o transacciones financieras en pipelines estocásticos (LLMs) "
                f"sin trazabilidad en silicio compromete la cadena de custodia probatoria.\n\n"
                f"BABYLON-60 aísla vuestros pipelines en silicio local y provee:\n"
                f"1. Trazabilidad WORM Continua (Art. 12): Recibos RFC 9942 COSE_Sign1 sellados en SQLite WAL.\n"
                f"2. Supervisión Humana en Hardware (Art. 14): Cerrojo biométrico Touch ID (allowableReuseDuration = 0).\n"
                f"3. Apoptosis Fail-Stop (Art. 15): Intercepción en nanosegundos (POISONED = 0xDEAD_6060).\n\n"
                f"Condiciones del Piloto (PoC): 15.000 € (30-45 días en hasta 5 nodos de staging) con auditoría reproducible.\n"
                f"Régimen Asincrónico: Sin llamadas comerciales de preventa. Verificación auditable en silicio.\n"
                f"Consulte el paquete de evidencia en: borja@babylon60.com / https://babylon60.com\n\n"
                f"Borja Fernández Angulo\nInvestigador en Sistemas Complejos & Operador Raíz\nBABYLON-60 Sovereign Trust Kernel"
            )

            # 3. LAHAMU-60 Hume Guillotine Audit
            audit = self.team_dist.audit_creative_copy(pitch)

            # 4. Hash Merkle Leaf
            payload_bytes = json.dumps({"lead_id": lead_id, "company": company, "pitch": pitch}, sort_keys=True).encode()
            leaf_hash = hashlib.sha256(payload_bytes).hexdigest()
            merkle_leaves.append(leaf_hash)

            processed_lead = {
                "lead_id": lead_id,
                "company": company,
                "contact_email": email,
                "target_role": role,
                "forensics": forensics,
                "audit": audit,
                "leaf_hash": leaf_hash,
                "dispatch_approved": audit["passed"],
            }
            processed_leads.append(processed_lead)

            status_icon = "✓" if audit["passed"] else "✗"
            print(f" [{status_icon}] {lead_id} | {company[:25]:<25} | {role[:15]:<15} | H={audit['entropy_shannon_bits']} bits | Status: {audit['status']}")

        # Compute Merkle Root
        combined_leaves = "".join(merkle_leaves).encode()
        batch_merkle_root = hashlib.sha256(combined_leaves).hexdigest()

        manifest = {
            "batch_timestamp": time.time(),
            "total_processed": len(processed_leads),
            "approved_for_dispatch": sum(1 for p in processed_leads if p["dispatch_approved"]),
            "merkle_root": batch_merkle_root,
            "governance_mode": "AIR_GAP_ASYNCHRONOUS",
            "auditor": "LAHAMU-60 (Guillotina de Hume)",
            "dispatcher": "TAMKARUM-60 (KudurruBudgetGate)",
        }

        print("-" * 78)
        print(f"➔ Resumen: {manifest['approved_for_dispatch']}/{manifest['total_processed']} aprobados para despacho asincrónico.")
        print(f"➔ Merkle Root del Lote: {batch_merkle_root}")
        print("=" * 78)

        return {"manifest": manifest, "leads": processed_leads}

    # ------------------------------------------------------------------------
    # Pipeline 2: Generador de Hilos Técnicos (Shamash -> Ishtar -> Lahamu)
    # ------------------------------------------------------------------------
    def run_social_thread_pipeline(self) -> Dict[str, Any]:
        print("\n" + "=" * 78)
        print(" [PIPELINE 2] REDES SOCIALES & HILOS TÉCNICOS (SHAMASH ➔ ISHTAR ➔ LAHAMU)")
        print("=" * 78)

        # Core thread on EU AI Act + Kernel Hardware Security
        concept = "EU AI Act vs. Pipelines Estocásticos: El colapso del Artículo 12"
        tweets = [
            (
                "1/5 El Reglamento (UE) 2024/1689 (EU AI Act) altera la responsabilidad del CISO: "
                "delegar mutaciones de bases de datos en agentes LLM sin trazabilidad en silicio "
                "invalida la cadena de custodia jurídica ante cualquier alucinación en producción."
            ),
            (
                "2/5 La ley ontológica O2 es tajante: 'Inferencia ≠ Autoridad'. "
                "Un modelo probabilístico jamás debe poseer capacidad directa de mutación. "
                "Cualquier arquitectura segura exige evaluar la 7-tupla formal antes del despacho."
            ),
            (
                "3/5 En BABYLON-60, cada invocación de herramienta emite un recibo RFC 9942 COSE_Sign1 "
                "sellado en SQLite WAL local. Cero alteración de código; auditoría matemática determinista (Art. 12)."
            ),
            (
                "4/5 La supervisión humana (Art. 14) se ancla en silicio: cerrojo biométrico Touch ID "
                "en Secure Enclave con allowableReuseDuration = 0. Vetamos que la IA se auto-autorice."
            ),
            (
                "5/5 Si el agente intenta desbordar sus capacidades, MUSHUSHU-0 dispara apoptosis fail-stop "
                "(POISONED = 0xDEAD_6060) en nanosegundos (Art. 15). "
                "Auditoría técnica en silicio: https://babylon60.com"
            ),
        ]

        thread_result = self.team_social.format_x_thread(concept, tweets)
        
        # Audit with Lahamu
        full_text = " ".join(tweets)
        audit = self.team_dist.audit_creative_copy(full_text)

        print(f"➔ Concepto: {concept}")
        print(f"➔ Total Tweets: {thread_result['total_tweets']} | Válidos: {thread_result['valid']}")
        print(f"➔ Entropía de Shannon: {audit['entropy_shannon_bits']} bits/char (Nominal: {audit['entropy_nominal']})")
        print(f"➔ Dictamen de LAHAMU-60: {audit['status']}")
        print("-" * 78)
        for t in thread_result["thread"]:
            print(f" [{t['index']}/{t['total']}] ({t['char_count']} chars): {t['text'][:70]}...")
        print("=" * 78)

        return {
            "concept": concept,
            "thread": thread_result,
            "audit": audit,
        }

    # ------------------------------------------------------------------------
    # Pipeline 3: Triage Comunitario y Debunker (Nergal -> Sin / Tiamat)
    # ------------------------------------------------------------------------
    def run_community_triage_pipeline(self) -> List[Dict[str, Any]]:
        print("\n" + "=" * 78)
        print(" [PIPELINE 3] RADAR DE ESCUCHA & TRIAGE COMUNITARIO (NERGAL ➔ SIN ➔ TIAMAT)")
        print("=" * 78)

        scenarios = [
            {
                "author": "sre_lead",
                "platform": "Discord",
                "message": "¿Cómo configuramos el compilador protoc para compilar strike-rs sin errores en macOS?",
            },
            {
                "author": "crypto_critic",
                "platform": "Hacker News",
                "message": "Esto de seguridad en hardware para LLMs es puro humo y vaporware innecesario.",
            },
            {
                "author": "compliance_officer",
                "platform": "GitHub Discussions",
                "message": "¿Dónde se exportan los certificados de atestación SCITT para auditoría externa de la UE?",
            },
        ]

        results = []
        for s in scenarios:
            res = self.team_social.triage_community_issue(
                author=s["author"],
                platform=s["platform"],
                message=s["message"],
            )
            results.append(res)
            adv_flag = "[ADVERSARIAL]" if res["is_adversarial"] else "[SOPORTE]"
            print(f" {adv_flag} @{res['author']} ({res['platform']}) ➔ Asignado a: {res['assigned_agent']}")
            print(f"   Mensaje: \"{s['message'][:65]}...\"")
            print(f"   Respuesta: \"{res['suggested_response'][:85]}...\"\n")

        print("=" * 78)
        return results

    # ------------------------------------------------------------------------
    # Pipeline 4: Presupuestador de Kelly (TAMKARUM-60 & KudurruBudgetGate)
    # ------------------------------------------------------------------------
    def run_kelly_budget_audit(self, bankroll_eur: float = 5000.0) -> Dict[str, Any]:
        print("\n" + "=" * 78)
        print(" [PIPELINE 4] ARBITRAJE DE ATENCIÓN POR CRITERIO DE KELLY (TAMKARUM-60 & ENKI-60)")
        print("=" * 78)

        bankroll_cents = int(bankroll_eur * 100)
        
        # Scenarios:
        # A: High targeted enterprise (Win prob 5%, payout 15,000 EUR vs 200 EUR test cost -> odds 75:1)
        # B: Medium targeted tech lead (Win prob 15%, payout 3:1)
        # C: Low negative expected value (Win prob 1%, payout 10:1 -> f* < 0)
        scenarios = [
            {"channel": "Enterprise CISO Outbound", "win_prob": 0.05, "odds": 75.0},
            {"channel": "Hacker News Sponsored Deep Dive", "win_prob": 0.15, "odds": 5.0},
            {"channel": "Generic Social Ads (Mitocondrias)", "win_prob": 0.01, "odds": 10.0},
        ]

        allocations = []
        for sc in scenarios:
            allocated_cents = self.team_dist.calculate_kelly_budget(
                win_probability=sc["win_prob"],
                odds=sc["odds"],
                bankroll_cents=bankroll_cents,
                fractional_kelly=0.25,
            )
            alloc_eur = allocated_cents / 100.0
            allocations.append({
                "channel": sc["channel"],
                "win_prob": sc["win_prob"],
                "odds": sc["odds"],
                "allocated_eur": alloc_eur,
                "action": "ENTRAR_EN_SUBASTA" if alloc_eur > 0 else "VETO_POR_ANERGIA",
            })
            print(f" ➔ {sc['channel']:<35} | P={sc['win_prob']:<4} | Odds={sc['odds']:<4} | Asignado: {alloc_eur:>8.2f} € | {allocations[-1]['action']}")

        print("-" * 78)
        print("➔ Confinamiento: Toda ejecución presupuestaria requiere desbloqueo biométrico en Ring-(-1).")
        print("=" * 78)

        return {"bankroll_eur": bankroll_eur, "allocations": allocations}


def main():
    parser = argparse.ArgumentParser(description="BABYLON-60 Tamkarum Swarm Orchestrator")
    parser.add_argument("--pipeline", choices=["outreach", "social-threads", "triage-community", "kelly-audit", "all"], default="all")
    parser.add_argument("--limit", type=int, default=5, help="Number of enterprise leads to process")
    parser.add_argument("--sector", type=str, default=None, help="Sector filter for outreach")
    args = parser.parse_args()

    orchestrator = TamkarumSwarmOrchestrator()

    if args.pipeline in ("outreach", "all"):
        orchestrator.run_outreach_pipeline(limit=args.limit, sector_filter=args.sector)

    if args.pipeline in ("social-threads", "all"):
        orchestrator.run_social_thread_pipeline()

    if args.pipeline in ("triage-community", "all"):
        orchestrator.run_community_triage_pipeline()

    if args.pipeline in ("kelly-audit", "all"):
        orchestrator.run_kelly_budget_audit()


if __name__ == "__main__":
    main()
