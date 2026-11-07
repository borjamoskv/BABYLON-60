#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ DISTRIBUTION, DESIGN & SOCIAL SWARMS | TESTS | STATE: C5-REAL
# ============================================================================
"""
Unit and Invariant Tests for BABYLON-60 Marketing, Design, Social Media & Community Swarms.
"""

from agents_archi import (
    SwarmRouter,
    TopologyTarget,
    DistributionDesignTeam,
    AgentRole,
    SocialMediaTeam,
    SocialAgentRole,
)


def test_distribution_design_roster_completeness() -> None:
    """Verifies all 6 canonical distribution & design agents are registered with strict invariants."""
    team = DistributionDesignTeam.list_team()
    assert len(team) == 6
    roles = {a.role for a in team}
    assert roles == {
        AgentRole.TAMKARUM_GROWTH,
        AgentRole.NIMROD_HUNTER,
        AgentRole.ISHTAR_DESIGN,
        AgentRole.GUDEA_SCRIBE,
        AgentRole.KISHAR_MOTION,
        AgentRole.LAHAMU_GUARDIAN,
    }

    tamkarum = DistributionDesignTeam.get_agent(AgentRole.TAMKARUM_GROWTH)
    assert tamkarum.ring == 1
    assert "KudurruBudgetGate" in tamkarum.system_role_description

    ishtar = DistributionDesignTeam.get_agent(AgentRole.ISHTAR_DESIGN)
    assert ishtar.ring == 2
    assert "Brutalist" in ishtar.title


def test_social_media_roster_completeness() -> None:
    """Verifies all 5 canonical social media & community agents are registered."""
    team = SocialMediaTeam.list_team()
    assert len(team) == 5
    roles = {a.role for a in team}
    assert roles == {
        SocialAgentRole.SHAMASH_SOCIAL,
        SocialAgentRole.NERGAL_RADAR,
        SocialAgentRole.SIN_COMMUNITY,
        SocialAgentRole.TIAMAT_DEBUNKER,
        SocialAgentRole.ENKIDU_ENGAGEMENT,
    }

    shamash = SocialMediaTeam.get_agent(SocialAgentRole.SHAMASH_SOCIAL)
    assert "X (Twitter)" in shamash.target_platforms
    assert shamash.ring == 2

    tiamat = SocialMediaTeam.get_agent(SocialAgentRole.TIAMAT_DEBUNKER)
    assert tiamat.ring == 1


def test_swarm_router_distribution_and_social_dispatch() -> None:
    """Tests exact and typo-tolerant routing for marketing, design, and social media intents."""
    # 1. Distribution & Design intents
    target, conf = SwarmRouter.route_query("necesito el equipo de marketing para lanzar campaña")
    assert target == TopologyTarget.DISTRIBUTION_DESIGN
    assert conf >= 0.8

    target, conf = SwarmRouter.route_query("ajusta los tokens de diseño brutalista de ishtar")
    assert target == TopologyTarget.DISTRIBUTION_DESIGN
    assert conf >= 0.8

    # 2. Social Media & Community intents
    target, conf = SwarmRouter.route_query("crea el hilo de twitter para el lanzamiento")
    assert target == TopologyTarget.SOCIAL_MEDIA_COMMUNITY
    assert conf >= 0.8

    target, conf = SwarmRouter.route_query("comunity manager para responder en discord")
    assert target == TopologyTarget.SOCIAL_MEDIA_COMMUNITY
    assert conf >= 0.8

    target, conf = SwarmRouter.route_query("radar de reddit r/LocalLLaMA")
    assert target == TopologyTarget.SOCIAL_MEDIA_COMMUNITY
    assert conf >= 0.8


def test_kelly_criterion_allocation() -> None:
    """Tests ENKI-60 Kelly Criterion fractional budget calculation for Tamkarum."""
    # Positive edge: win_prob 0.6, odds 2.0 (payout 2:1), bankroll 100,000 cents (1,000 EUR)
    # f* = (0.6 * 2 - 0.4) / 2 = (1.2 - 0.4) / 2 = 0.8 / 2 = 0.40
    # fractional Kelly (0.25) -> 0.40 * 0.25 = 0.10 -> 10% of 100,000 = 10,000 cents
    allocation = DistributionDesignTeam.calculate_kelly_budget(
        win_probability=0.6,
        odds=2.0,
        bankroll_cents=100000,
        fractional_kelly=0.25,
    )
    assert allocation == 10000

    # Negative edge: win_prob 0.3, odds 1.5
    # f* = (0.3 * 1.5 - 0.7) / 1.5 = (0.45 - 0.7) / 1.5 < 0 -> 0 cents
    zero_allocation = DistributionDesignTeam.calculate_kelly_budget(
        win_probability=0.3,
        odds=1.5,
        bankroll_cents=100000,
    )
    assert zero_allocation == 0


def test_lahamu_hume_guillotine_cheap_talk_filter() -> None:
    """Verifies that LAHAMU-60 purges cheap talk and measures Shannon entropy."""
    # Dirty marketing copy with prohibited words
    dirty_copy = (
        "Nuestra solución mágica impulsada por IA es revolucionaria y ofrece "
        "seguridad absoluta y cero riesgo para tu empresa. Agenda un café virtual!"
    )
    verdict = DistributionDesignTeam.audit_creative_copy(dirty_copy)
    assert verdict["passed"] is False
    assert verdict["status"] == "REJECT_FAIL_CLOSED"
    assert len(verdict["violations"]) >= 3

    # Clean high-exergy copy
    clean_copy = (
        "BABYLON-60 aísla mutaciones agénticas mediante recibos criptográficos RFC 9942 "
        "COSE_Sign1 sellados en SQLite WAL local. Implementa controles formales del EU AI Act."
    )
    clean_verdict = DistributionDesignTeam.audit_creative_copy(clean_copy)
    assert clean_verdict["passed"] is True
    assert clean_verdict["status"] == "PASS"
    assert clean_verdict["entropy_nominal"] is True
    assert len(clean_verdict["violations"]) == 0


def test_social_media_thread_validation() -> None:
    """Verifies SHAMASH-60's tweet length and thread formatting rules."""
    tweets = [
        "1/3 El colapso de seguridad en pipelines LLM surge al confundir inferencia con autoridad (Ley O2).",
        "2/3 BABYLON-60 implementa la 7-tupla canónica de decisión antes de cualquier mutación de base de datos.",
        "3/3 Los recibos COSE_Sign1 se anclan en SQLite WAL local. Verificación on-premise en silicio: https://babylon60.com",
    ]
    thread_result = SocialMediaTeam.format_x_thread("Arquitectura de Seguridad EU AI Act", tweets)
    assert thread_result["valid"] is True
    assert thread_result["total_tweets"] == 3

    # Tweet too long
    too_long = ["A" * 290]
    invalid_thread = SocialMediaTeam.format_x_thread("Test", too_long)
    assert invalid_thread["valid"] is False
    assert len(invalid_thread["violations"]) == 1


def test_community_issue_triage() -> None:
    """Verifies community triage dispatches adversarial skepticism to Tiamat and regular support to Sin."""
    # Adversarial question
    adv_result = SocialMediaTeam.triage_community_issue(
        author="critic_99",
        platform="Hacker News",
        message="Esto parece vaporware y vendehumo, langchain es mejor y gratis.",
    )
    assert adv_result["is_adversarial"] is True
    assert adv_result["assigned_agent"] == SocialAgentRole.TIAMAT_DEBUNKER.value
    assert "KUDURRU-64" in adv_result["suggested_response"]

    # Constructive engineering question
    eng_result = SocialMediaTeam.triage_community_issue(
        author="dev_rust",
        platform="Discord",
        message="¿Cómo compilo los crates con protoc provisionado en macOS?",
    )
    assert eng_result["is_adversarial"] is False
    assert eng_result["assigned_agent"] == SocialAgentRole.SIN_COMMUNITY.value
    assert "cargo check" in eng_result["suggested_response"]
