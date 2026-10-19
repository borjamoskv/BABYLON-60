#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ DISTRIBUTION & DESIGN SWARM TOPOLOGY | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
Sovereign Distribution, Marketing & Design Multi-Agent Swarm (MASS Framework).

Comprises 6 canonical sexagesimal agents partitioned across Ring-1 and Ring-2:
  1. TAMKARUM-60  (Ring-1): Sovereign Growth & Arbitrage Engine (Kelly Criterion)
  2. NIMROD-60    (Ring-2): Lead Intelligence & Regulatory Forensics Hunter (EU AI Act Arts 9-15)
  3. ISHTAR-60    (Ring-2): Brutalist Visual Architect & UI/UX Designer (Zero-JS / SSR / TUI)
  4. GUDEA-60     (Ring-2): Epistemic Scribe & High-Exergy Copywriter (Shannon Density)
  5. KISHAR-60    (Ring-2): Kinetic Transducer & Motion Synthesizer (Remotion / Terminal Cinematics)
  6. LAHAMU-60    (Ring-1): Hume Guillotine & Brand Sentinel (Popperian Verification / Fail-Closed)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List
import math
import re


class AgentRole(Enum):
    TAMKARUM_GROWTH = "tamkarum_growth"
    NIMROD_HUNTER = "nimrod_hunter"
    ISHTAR_DESIGN = "ishtar_design"
    GUDEA_SCRIBE = "gudea_scribe"
    KISHAR_MOTION = "kishar_motion"
    LAHAMU_GUARDIAN = "lahamu_guardian"


@dataclass(frozen=True)
class AgentSpecification:
    """Rigid structural specification for each agent in the swarm."""

    role: AgentRole
    canonical_name: str
    title: str
    ring: int
    system_role_description: str
    loss_function: str
    circuit_breaker: str
    allowed_tools: List[str]
    input_contracts: List[str]
    output_contracts: List[str]


class DistributionDesignTeam:
    """
    Orchestration topology and governance engine for BABYLON-60's
    Growth, Outreach, Visual Identity and Audiovisual Transduction.
    """

    ROSTER: Dict[AgentRole, AgentSpecification] = {
        AgentRole.TAMKARUM_GROWTH: AgentSpecification(
            role=AgentRole.TAMKARUM_GROWTH,
            canonical_name="TAMKARUM-60",
            title="Director Soberano de Crecimiento & Arbitraje (GTM)",
            ring=1,
            system_role_description=(
                "Transductor de arbitraje en la Estepa. Gobierna el crecimiento B2B asincrónico, "
                "arbitra subastas RTB según el Criterio de Kelly (ENKI-60), audita la cola de leads "
                "y despacha contratos bajo el cerrojo KudurruBudgetGate (64B align(64))."
            ),
            loss_function="Maximizar Liquidez Soberana Neta / Minimizar CAC Explotativo",
            circuit_breaker="MUSHUSHU-0 (0xDEAD_6060) si ROAS < 1.0 tras 60 ciclos sexagesimales",
            allowed_tools=[
                "tamkarum_review",
                "tamkarum_audit",
                "tamkarum_launch_dryrun",
                "kudurru_gate_eval",
            ],
            input_contracts=["QualifiedLeadEnrichment", "ValidatedCreativeAsset"],
            output_contracts=["OutreachCampaignBatch", "KellyAllocationPlan"],
        ),
        AgentRole.NIMROD_HUNTER: AgentSpecification(
            role=AgentRole.NIMROD_HUNTER,
            canonical_name="NIMROD-60",
            title="Cazador Forense B2B & Inteligencia Regulatoria",
            ring=2,
            system_role_description=(
                "Mapeo forense de infraestructuras corporativas con IA de alto riesgo. "
                "Detecta brechas de trazabilidad (Art 12), gobernanza (Art 14) y robustez (Art 15) "
                "del EU AI Act. Extrae y enriquece decisores clave (CISOs, DPOs, VPs de Seguridad)."
            ),
            loss_function="Maximizar Precisión de Brecha Regulatoria / Cero Falsos Positivos de Spam",
            circuit_breaker="Apoptosis si la tasa de rebote o falsos positivos supera el 2%",
            allowed_tools=[
                "search_web",
                "read_url_content",
                "parse_tech_stack",
                "eu_ai_act_risk_scorer",
            ],
            input_contracts=["RawSectorCriteria", "DomainTarget"],
            output_contracts=["ForensicLeadDossier", "RegulatoryVulnerabilityScore"],
        ),
        AgentRole.ISHTAR_DESIGN: AgentSpecification(
            role=AgentRole.ISHTAR_DESIGN,
            canonical_name="ISHTAR-60",
            title="Arquitecto Visual & Diseñador Brutalista UI/UX",
            ring=2,
            system_role_description=(
                "Dirección de arte industrial y brutalista. Paleta monocromo azabache (#0a0a0a), "
                "fósforo ámbar (#ffb000) y verde terminal (#00ff66). Tipografía monospace técnica "
                "(JetBrains Mono / Berkeley Mono). Interfaces Zero-JS / SSR Astro (babylon60.com) "
                "y dashboards pasivos TUI (babylon top)."
            ),
            loss_function="Maximizar Exergía Visual & Fidelidad Topológica / Aniquilar Virtual DOM Bloat",
            circuit_breaker="Rechazo automático ante cualquier plantilla genérica SaaS o gradientes pastel",
            allowed_tools=[
                "write_to_file",
                "replace_file_content",
                "render_astro_preview",
                "generate_svg_schematics",
            ],
            input_contracts=["ArchitectureManifest", "UIRequirementSpec"],
            output_contracts=["ZeroJsComponent", "BrutalistDesignTokens", "VectorSchematics"],
        ),
        AgentRole.GUDEA_SCRIBE: AgentSpecification(
            role=AgentRole.GUDEA_SCRIBE,
            canonical_name="GUDEA-60",
            title="Escriba Epistémico & Copywriter de Alta Exergía",
            ring=2,
            system_role_description=(
                "Redactor de pitches enterprise asincrónicos, whitepapers técnicos y defensas epistémicas. "
                "Aplica la densidad de información de Shannon (H in [3.79, 5.88] bits/char). "
                "Purga el cheap talk, superlativos vacíos y llamadas comerciales síncronas."
            ),
            loss_function="Maximizar Densidad de Shannon / Minimizar Entropía Retórica (Cheap Talk)",
            circuit_breaker="Apoptosis ante palabras prohibidas ('revolucionario', 'disruptivo', 'impulsado por IA')",
            allowed_tools=[
                "write_to_file",
                "replace_file_content",
                "compute_shannon_entropy",
                "verify_clauses_eu_ai_act",
            ],
            input_contracts=["ForensicLeadDossier", "ProductEvidenceLock"],
            output_contracts=["AsynchronousEnterprisePitch", "TechnicalWhitepaperChunk"],
        ),
        AgentRole.KISHAR_MOTION: AgentSpecification(
            role=AgentRole.KISHAR_MOTION,
            canonical_name="KISHAR-60",
            title="Transductor Cinético & Sintetizador Audiovisual",
            ring=2,
            system_role_description=(
                "Motion design programático y cinematografía de terminal. Genera animaciones reactivas "
                "en código (Remotion / WebGL Canvas), grabaciones cinéticas de terminal (asciinema / TUI) "
                "y explicaciones visuales de las transiciones entre Ring-0 y Ring-2."
            ),
            loss_function="Maximizar Comprensión Dinámica de Hardware / Cero Relleno Cinematográfico",
            circuit_breaker="Descarte si el renderizado introduce artefactos de compresión no deterministas",
            allowed_tools=[
                "render_remotion_composition",
                "generate_terminal_asciicast",
                "ffmpeg_transcode_raw",
            ],
            input_contracts=["TerminalExecutionTrace", "MotionStoryboard"],
            output_contracts=["ProgrammaticVideoMp4", "TerminalAsciiCast"],
        ),
        AgentRole.LAHAMU_GUARDIAN: AgentSpecification(
            role=AgentRole.LAHAMU_GUARDIAN,
            canonical_name="LAHAMU-60",
            title="Centinela de Marca & Guillotina de Hume",
            ring=1,
            system_role_description=(
                "Auditor fail-closed de toda pieza antes de su publicación o despacho exterior. "
                "Verifica que todo claim textual esté indexado en CLAIMS.toml y respaldado por tests "
                "en silicio. Veta cualquier sugerencia de invulnerabilidad absoluta o mito hagiográfico."
            ),
            loss_function="Maximizar Honestidad Falsable / Tolerancia Cero a la Confabulación",
            circuit_breaker="FAIL-CLOSED inmediato ante cualquier claim no atestado en silicio",
            allowed_tools=[
                "audit_claims_lock",
                "verify_silicon_receipts",
                "humes_guillotine_eval",
            ],
            input_contracts=["DraftPitchOrCreativeAsset", "TargetAudienceMetadata"],
            output_contracts=["AttestedPublicationCertificate", "AuditVetoReport"],
        ),
    }

    # Cheap talk blacklist (Prohibited marketing words)
    CHEAP_TALK_BLACKLIST = [
        r"\brevolucionari[oa]s?\b",
        r"\bdisruptiv[oa]s?\b",
        r"\bpotenciad[oa] por ia\b",
        r"\bimpulsad[oa] por ia\b",
        r"\bsolución mágica\b",
        r"\b100% invulnerables?\b",
        r"\bseguridad absoluta\b",
        r"\binfalibles?\b",
        r"\bcero riesgo\b",
        r"\bllamada de 15 minutos\b",
        r"\bagenda un café virtual\b",
    ]

    @classmethod
    def get_agent(cls, role: AgentRole) -> AgentSpecification:
        """Retrieves exact agent specification."""
        return cls.ROSTER[role]

    @classmethod
    def list_team(cls) -> List[AgentSpecification]:
        """Returns the full roster of the distribution & design team."""
        return list(cls.ROSTER.values())

    @classmethod
    def audit_creative_copy(cls, copy_text: str) -> Dict[str, Any]:
        """
        Executes LAHAMU-60's Hume Guillotine and anti-cheap-talk filter on candidate text.
        Returns Pass/Fail verdict, detected violations, and computed Shannon entropy.
        """
        violations: List[str] = []
        lower_text = copy_text.lower()

        # 1. Blacklist check
        for pattern in cls.CHEAP_TALK_BLACKLIST:
            matches = re.findall(pattern, lower_text)
            if matches:
                violations.append(f"Cheap Talk Detectado: '{matches[0]}'")

        # 2. Shannon Entropy metric (H)
        char_counts: Dict[str, int] = {}
        for char in copy_text:
            char_counts[char] = char_counts.get(char, 0) + 1

        entropy = 0.0
        total_len = len(copy_text)
        if total_len > 0:
            for count in char_counts.values():
                p = count / total_len
                entropy -= p * math.log2(p)

        # 3. Verdict
        passed = len(violations) == 0
        status = "PASS" if passed else "REJECT_FAIL_CLOSED"

        return {
            "status": status,
            "passed": passed,
            "entropy_shannon_bits": round(entropy, 3),
            "entropy_nominal": 3.79 <= entropy <= 5.88,
            "violations": violations,
            "auditor": "LAHAMU-60 (Guillotina de Hume)",
        }

    @classmethod
    def calculate_kelly_budget(
        cls,
        win_probability: float,
        odds: float,
        bankroll_cents: int,
        fractional_kelly: float = 0.25,
    ) -> int:
        """
        Computes TAMKARUM-60's optimal Kelly Criterion allocation (in cents)
        for RTB attention auctions or customer acquisition campaigns.

        Formula: f* = (p * b - q) / b
        where:
          p = win_probability
          q = 1 - p
          b = net odds received (payout / risk)
        Uses fractional Kelly (default 0.25) to protect bankroll against volatility.
        """
        if not (0.0 < win_probability < 1.0):
            return 0
        if odds <= 0.0:
            return 0

        p = win_probability
        q = 1.0 - p
        b = odds

        f_star = (p * b - q) / b
        if f_star <= 0.0:
            return 0  # Negative expectation: do not enter auction

        # Apply conservative fractional Kelly and cap at bankroll
        allocated_ratio = min(1.0, max(0.0, f_star * fractional_kelly))
        allocated_cents = int(bankroll_cents * allocated_ratio)
        return allocated_cents

    @classmethod
    def simulate_pipeline_handoff(
        cls,
        lead_id: str,
        company: str,
        sector: str,
        contact_role: str,
    ) -> Dict[str, Any]:
        """
        Simulates the end-to-end multi-agent execution pipeline:
          NIMROD-60 (Lead Forensic) -> GUDEA-60 (Copywriting) ->
          LAHAMU-60 (Audit) -> TAMKARUM-60 (Outreach Dispatch).
        """
        # Step 1: NIMROD-60 forensic analysis
        forensic_dossier = {
            "lead_id": lead_id,
            "company": company,
            "sector": sector,
            "target_role": contact_role,
            "eu_ai_act_risk_tier": "High Risk (Annex III / Autonomous Agents)",
            "applicable_articles": ["Art. 12 (WORM logging)", "Art. 14 (Human oversight)", "Art. 15 (Fail-stop)"],
            "vulnerability_rationale": "High-risk agentic pipeline without hardware-attested audit trail.",
        }

        # Step 2: GUDEA-60 craft pitch
        draft_pitch = (
            f"Asunto: Controles Ring-0 y Trazabilidad WORM (EU AI Act) para los agentes de {company}\n\n"
            f"Estimado equipo de Seguridad liderado por {contact_role},\n"
            f"La entrada en aplicación del Reglamento (UE) 2024/1689 para sistemas de alto riesgo "
            f"altera la responsabilidad corporativa: ejecutar mutaciones irreversibles en bases de datos "
            f"mediante pipelines estocásticos sin trazabilidad en silicio compromete la cadena de custodia.\n"
            f"BABYLON-60 aísla vuestros pipelines en silicio local bajo controles formales (Arts. 12, 14 y 15).\n"
            f"Piloto cerrado: 15.000 € (30-45 días, 5 nodos de staging) con auditoría determinista en silicio.\n"
            f"Consulte el paquete de evidencia en borja@babylon60.com / https://babylon60.com\n\n"
            f"Borja Fernández Angulo — Operador Raíz, BABYLON-60"
        )

        # Step 3: LAHAMU-60 audit
        audit_verdict = cls.audit_creative_copy(draft_pitch)

        # Step 4: TAMKARUM-60 dispatch decision
        dispatch_authorized = audit_verdict["passed"]

        return {
            "lead_id": lead_id,
            "forensic_enrichment": forensic_dossier,
            "draft_copy": draft_pitch,
            "audit": audit_verdict,
            "dispatch_ready": dispatch_authorized,
            "governance_sink": "KudurruBudgetGate (Pending Ring-(-1) Touch ID Attestation)",
        }
