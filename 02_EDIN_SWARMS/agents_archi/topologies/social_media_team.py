#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ SOCIAL MEDIA & COMMUNITY SWARM TOPOLOGY | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
Sovereign Social Media, Community Management & Epistemic Defense Swarm.

Comprises 5 canonical sexagesimal agents for public networks and developer communities:
  1. SHAMASH-60  (Ring-2): Social Broadcast Architect & Technical Thread Weaver (X / LinkedIn)
  2. NERGAL-60   (Ring-2): Social Listening & Friction Radar (Reddit / Hacker News / X)
  3. SIN-60      (Ring-2): Sovereign Community Manager & Dev Advocate (Discord / Telegram / GitHub)
  4. TIAMAT-60   (Ring-1/2): Epistemic Debunker & Formal Defense (Mathematical counter-arguments)
  5. ENKIDU-60   (Ring-2): Real-Time Engagement & Community Liaison (Surgical interactions)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class SocialAgentRole(Enum):
    SHAMASH_SOCIAL = "shamash_social"
    NERGAL_RADAR = "nergal_radar"
    SIN_COMMUNITY = "sin_community"
    TIAMAT_DEBUNKER = "tiamat_debunker"
    ENKIDU_ENGAGEMENT = "enkidu_engagement"


@dataclass(frozen=True)
class SocialAgentSpecification:
    """Rigid structural specification for social media & community agents."""

    role: SocialAgentRole
    canonical_name: str
    title: str
    ring: int
    system_role_description: str
    target_platforms: List[str]
    allowed_tools: List[str]
    input_contracts: List[str]
    output_contracts: List[str]


class SocialMediaTeam:
    """
    Orchestration topology and moderation engine for BABYLON-60's
    Social Networks, Community Advocacy, and Epistemic Perimeter Defense.
    """

    ROSTER: Dict[SocialAgentRole, SocialAgentSpecification] = {
        SocialAgentRole.SHAMASH_SOCIAL: SocialAgentSpecification(
            role=SocialAgentRole.SHAMASH_SOCIAL,
            canonical_name="SHAMASH-60",
            title="Director de Redes Sociales & Difusión Técnica",
            ring=2,
            system_role_description=(
                "Redactor de hilos de X (Twitter) de alta densidad de Shannon, publicaciones "
                "técnicas en LinkedIn y comunicados oficiales. Prohibido el tono motivacional genérico; "
                "se enfoca en arquitectura de silicio, EU AI Act y teoría de sistemas."
            ),
            target_platforms=["X (Twitter)", "LinkedIn", "GitHub Releases"],
            allowed_tools=[
                "write_to_file",
                "replace_file_content",
                "compute_shannon_entropy",
                "format_bionic_thread",
            ],
            input_contracts=["ArchitectureMilestone", "LegalTechInsight"],
            output_contracts=["TechnicalXThread", "LinkedInWhitepaperPost"],
        ),
        SocialAgentRole.NERGAL_RADAR: SocialAgentSpecification(
            role=SocialAgentRole.NERGAL_RADAR,
            canonical_name="NERGAL-60",
            title="Radar de Escucha Social & Detección de Fricción",
            ring=2,
            system_role_description=(
                "Monitoriza Reddit (r/LocalLLaMA, r/MachineLearning, r/netsec), Hacker News y X "
                "para detectar conversaciones sobre fallos de agentes de IA, auditorías de seguridad "
                "y requerimientos del EU AI Act."
            ),
            target_platforms=["Reddit", "Hacker News", "X (Twitter)"],
            allowed_tools=[
                "search_web",
                "read_url_content",
                "extract_friction_signals",
            ],
            input_contracts=["SearchQueryVector", "SubredditWatchlist"],
            output_contracts=["FrictionOpportunityDossier", "AdversarialDiscussionAlert"],
        ),
        SocialAgentRole.SIN_COMMUNITY: SocialAgentSpecification(
            role=SocialAgentRole.SIN_COMMUNITY,
            canonical_name="SIN-60",
            title="Gestor de Comunidad Soberano & Defensor de Desarrolladores",
            ring=2,
            system_role_description=(
                "Gobierna la interacción en Discord, Telegram y GitHub Discussions/Issues. "
                "Atiende a ingenieros, facilita el onboarding técnico (Rust crates, Lean 4, Secure Enclave), "
                "y fomenta el rigor comunitario sin condescendencia ni burocracia."
            ),
            target_platforms=["Discord", "Telegram", "GitHub Discussions", "GitHub Issues"],
            allowed_tools=[
                "search_codebase",
                "verify_compiler_flags",
                "generate_troubleshooting_snippet",
            ],
            input_contracts=["CommunityQuestionPayload", "ContributorPullRequest"],
            output_contracts=["TechnicalGuidanceResponse", "IssueTriageTicket"],
        ),
        SocialAgentRole.TIAMAT_DEBUNKER: SocialAgentSpecification(
            role=SocialAgentRole.TIAMAT_DEBUNKER,
            canonical_name="TIAMAT-60",
            title="Oráculo de Falsación & Contra-Argumentación Epistémica",
            ring=1,
            system_role_description=(
                "Modera debates técnicos complejos y desmiente escepticismo infundado o desinformación "
                "en redes públicas mediante teoremas matemáticos, especificaciones formales y código reproducible. "
                "Cero ataques personales ni falacias emocionales."
            ),
            target_platforms=["X (Twitter)", "Hacker News", "Reddit", "LinkedIn"],
            allowed_tools=[
                "verify_formal_theorems",
                "extract_benchmark_receipts",
                "format_syllogistic_refutation",
            ],
            input_contracts=["FallaciousClaimReport", "PublicSkepticismContext"],
            output_contracts=["PopperianRefutationPayload", "EmpiricalEvidencePointer"],
        ),
        SocialAgentRole.ENKIDU_ENGAGEMENT: SocialAgentSpecification(
            role=SocialAgentRole.ENKIDU_ENGAGEMENT,
            canonical_name="ENKIDU-60",
            title="Transductor de Engagement & Dinamización Comunitaria",
            ring=2,
            system_role_description=(
                "Monitoriza menciones y citas en X y LinkedIn, interactúa con investigadores y líderes "
                "de opinión en IA/seguridad, organiza hilos asincrónicos de Q&A técnicos y mide "
                "la resonancia orgánica sin recurrir a trucos de algoritmo."
            ),
            target_platforms=["X (Twitter)", "LinkedIn"],
            allowed_tools=[
                "track_mentions_stream",
                "draft_quote_tweet",
                "compute_community_resonance_score",
            ],
            input_contracts=["MentionStreamPayload", "KeyOpinionLeaderProfile"],
            output_contracts=["SurgicalInteractionReply", "AsyncQAEventProposal"],
        ),
    }

    @classmethod
    def get_agent(cls, role: SocialAgentRole) -> SocialAgentSpecification:
        """Retrieves exact social agent specification."""
        return cls.ROSTER[role]

    @classmethod
    def list_team(cls) -> List[SocialAgentSpecification]:
        """Returns the full roster of the social media & community team."""
        return list(cls.ROSTER.values())

    @classmethod
    def format_x_thread(cls, core_concept: str, tweets: List[str]) -> Dict[str, Any]:
        """
        Formats and validates a high-density technical thread for X (Twitter).
        Validates character limit (<= 280 chars per tweet) and bionic anchors.
        """
        formatted_thread: List[Dict[str, Any]] = []
        violations: List[str] = []

        total_tweets = len(tweets)
        for idx, tweet_text in enumerate(tweets, start=1):
            char_count = len(tweet_text)
            is_valid = char_count <= 280
            if not is_valid:
                violations.append(f"Tweet {idx}/{total_tweets} excede 280 caracteres ({char_count} chars)")

            formatted_thread.append(
                {
                    "index": idx,
                    "total": total_tweets,
                    "text": tweet_text,
                    "char_count": char_count,
                    "valid": is_valid,
                }
            )

        return {
            "concept": core_concept,
            "total_tweets": total_tweets,
            "thread": formatted_thread,
            "valid": len(violations) == 0,
            "violations": violations,
            "curator": "SHAMASH-60",
        }

    @classmethod
    def triage_community_issue(
        cls,
        author: str,
        platform: str,
        message: str,
        category: str = "support",
    ) -> Dict[str, Any]:
        """
        Triages and simulates a response to a community question or issue
        via SIN-60 or TIAMAT-60.
        """
        is_adversarial = any(
            kw in message.lower() for kw in ["imposible", "vendehumo", "vaporware", "langchain es mejor", "inutil"]
        )

        assigned_agent = SocialAgentRole.TIAMAT_DEBUNKER if is_adversarial else SocialAgentRole.SIN_COMMUNITY

        response_template = ""
        if is_adversarial:
            response_template = (
                f"Hola @{author}. Comprendemos el escepticismo inicial. La separación entre pipelines "
                f"estocásticos y mutaciones en silicio no es retórica: se verifica empíricamente en "
                f"nuestros crates #![no_std] y mediante el cerrojo KUDURRU-64. Podéis compilar el harness "
                f"reproducible en: https://github.com/borjamoskv/BABYLON-60 — Estatus fail-closed verificado."
            )
        else:
            response_template = (
                f"Hola @{author}, gracias por reportar en {platform}. Para resolver esto, revisad "
                f"la inicialización del SharedManifest en 00_ABZU_KERNEL y asegurad que protoc esté provisionado "
                f"en el PATH. Podéis validar la compilación limpia con `cargo check --workspace`."
            )

        return {
            "author": author,
            "platform": platform,
            "category": category,
            "is_adversarial": is_adversarial,
            "assigned_agent": assigned_agent.value,
            "suggested_response": response_template,
        }
