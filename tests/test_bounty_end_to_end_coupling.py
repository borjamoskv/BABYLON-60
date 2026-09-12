# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [PoC & Falsación Empírica] End-to-End Coupling: Bounties -> DeFi & WebKit
"""test_bounty_end_to_end_coupling.py - Certificación end-to-end de la cadena Ω-Bounty-Ingest.

Valida:
1. Sondeo y agregación de feeds (GitHub Advisories + Code4rena).
2. Empaquetado B60IPC y despacho a colas canónicas.
3. Inspección cuantitativa de bytecode y flags de Uniswap v4 (DeFiBytecodeScraper).
4. Detección de EIP-1153 (TSTORE/TLOAD) con evasión de operandos PUSH.
5. Triaje forense de memoria WebKit/JSC (Gigacage, IsoMalloc).
"""

from __future__ import annotations

import httpx
import pytest

from babylon60.bft.bounty_ring_dispatcher import BountyRingDispatcher
from babylon60.bft.defi_bytecode_scraper import (
    BEFORE_SWAP_FLAG,
    BEFORE_SWAP_RETURNS_DELTA_FLAG,
    DeFiBytecodeScraper,
    HookPermissions,
)
from babylon60.bft.saga1_ml_sentinel import Saga1MlSentinel, Saga1VulnerabilityClass
from babylon60.bft.webkit_memory_connector import WebKitMemoryConnector
from babylon60.transducers.bounty_feed_transducer import (
    BountyAdvisory,
    BountyDomain,
    BountyFeedTransducer,
)


def test_uniswap_v4_hook_permissions_and_eip1153_analysis() -> None:
    """Valida la extracción de la máscara de 14 bits y el desensamblado de EIP-1153."""
    scraper = DeFiBytecodeScraper()

    # 1. Dirección con flags: BEFORE_SWAP (bit 7) y BEFORE_SWAP_RETURNS_DELTA (bit 3)
    # (1 << 7) | (1 << 3) = 128 + 8 = 136 = 0x0088
    # Desplazado a los 14 bits superiores de 160 bits (160 - 14 = 146 bits de shift)
    # 0x0088 << 146 en hex -> address que inicia con 0x0088...
    flag_int = (BEFORE_SWAP_FLAG | BEFORE_SWAP_RETURNS_DELTA_FLAG) << (160 - 14)
    addr_hex = f"0x{flag_int:040x}"

    perms = HookPermissions.from_address(addr_hex)
    assert perms.before_swap is True
    assert perms.before_swap_returns_delta is True
    assert perms.after_swap is False

    # 2. Bytecode EVM con PUSH1 0x5d (no debe contarse como TSTORE) seguido de TSTORE real (0x5d)
    # 60 5d (PUSH1 0x5d) -> 5e (TLOAD) -> 5d (TSTORE) -> 00 (STOP)
    bytecode = "605d5e5d00"
    res = scraper.analyze_bytecode(bytecode, address=addr_hex)

    assert res.has_tstore is True
    assert res.has_tload is True
    assert res.tstore_count == 1  # Solo el TSTORE real, no el dato de PUSH1
    assert res.tload_count == 1
    assert res.risk_score > 0.5
    assert any("Hook Uniswap v4 detectado" in f for f in res.findings)
    assert any("Transient Storage activo" in f for f in res.findings)


def test_webkit_memory_triage_and_cage_escape_assessment() -> None:
    """Valida el triaje causal de memoria nativa en WebKit/JSC."""
    connector = WebKitMemoryConnector()

    advisory = BountyAdvisory(
        advisory_id="APPLE-WEBKIT-001",
        source="apple_security",
        title="WebKit Gigacage bypass via DFG JIT type confusion",
        target_ecosystem="webkit/jscore",
        domain=BountyDomain.DOMAIN_NATIVE,
        severity="critical",
        reference_url="https://support.apple.com/kb/HT200111",
        payload_summary="Out-of-bounds write in IsoMalloc through uncaged pointer",
        raw_fingerprint="sha3_webkit_fp",
    )

    triage = connector.triage_advisory(advisory)

    assert "Gigacage" in triage.affected_subsystems
    assert "IsoMalloc" in triage.affected_subsystems
    assert "JIT_Compiler" in triage.affected_subsystems
    assert triage.gigacage_bypass_risk is True
    assert triage.risk_score >= 0.9
    assert "vmmap" in triage.recommended_probe


@pytest.mark.asyncio
async def test_end_to_end_coupling_pipeline() -> None:
    """Flujo completo: Transductor -> B60IPC -> Despachador -> Scrapers de Dominio."""
    transducer = BountyFeedTransducer()
    dispatcher = BountyRingDispatcher()
    defi_scraper = DeFiBytecodeScraper()
    webkit_connector = WebKitMemoryConnector()

    # Simular entrada heterogénea de avisos
    raw_gh_advisory = {
        "ghsa_id": "GHSA-DEFI-4444",
        "summary": "Uniswap v4 hook transient storage reentrancy vulnerability",
        "description": "Exploit bytecode: 60005e5d",
        "severity": "high",
        "html_url": "https://github.com/advisories/GHSA-DEFI-4444",
        "vulnerabilities": [{"package": {"ecosystem": "solidity"}}],
    }

    raw_c4_repo_name = "2026-04-k2-defi-protocol"
    raw_c4_repo_url = "https://github.com/code-423n4/2026-04-k2-defi-protocol"

    raw_webkit_advisory = {
        "ghsa_id": "GHSA-WEBKIT-7777",
        "summary": "WebKit JavaScriptCore memory corruption in IsoMalloc",
        "description": "Heap use after free in IsoHeap allocation",
        "severity": "critical",
        "html_url": "https://github.com/advisories/GHSA-WEBKIT-7777",
        "vulnerabilities": [{"package": {"ecosystem": "cpp"}}],
    }

    raw_ai_advisory = {
        "ghsa_id": "GHSA-AI-9999",
        "summary": "PyTorch arbitrary code execution via unsafe torch.load deserialization",
        "description": "Pickle opcode injection in tensor checkpoint",
        "severity": "critical",
        "html_url": "https://github.com/advisories/GHSA-AI-9999",
        "vulnerabilities": [{"package": {"ecosystem": "pip"}}],
    }

    # 1. Transducción
    frame1 = transducer.normalize_github_advisory(raw_gh_advisory)
    assert frame1 is not None
    b60_frame1 = transducer.pack_advisory_to_b60ipc(frame1)

    frame2 = transducer.normalize_contest_repository(
        repo_name=raw_c4_repo_name,
        repo_url=raw_c4_repo_url,
        description="Uniswap v4 hooks and flash accounting",
        source="code4rena",
    )
    assert frame2 is not None
    b60_frame2 = transducer.pack_advisory_to_b60ipc(frame2)

    frame3 = transducer.normalize_github_advisory(raw_webkit_advisory)
    assert frame3 is not None
    b60_frame3 = transducer.pack_advisory_to_b60ipc(frame3)

    frame4 = transducer.normalize_github_advisory(raw_ai_advisory)
    assert frame4 is not None
    b60_frame4 = transducer.pack_advisory_to_b60ipc(frame4)

    # 2. Despacho por el bus en memoria
    dispatcher.dispatch_frame(b60_frame1)
    dispatcher.dispatch_frame(b60_frame2)
    dispatcher.dispatch_frame(b60_frame3)
    dispatcher.dispatch_frame(b60_frame4)

    depths = dispatcher.get_queue_depths()
    assert depths["evm"] == 2
    assert depths["native"] == 1
    assert depths["ai"] == 1

    # 3. Drenaje y análisis especializado
    evm_advisories = dispatcher.drain_domain(BountyDomain.DOMAIN_EVM)
    assert len(evm_advisories) == 2
    analysis_results = defi_scraper.process_advisories(evm_advisories)
    assert len(analysis_results) == 2
    assert dispatcher.get_queue_depths()["evm"] == 0

    native_advisories = dispatcher.drain_domain(BountyDomain.DOMAIN_NATIVE)
    assert len(native_advisories) == 1
    triage_results = webkit_connector.process_advisories(native_advisories)
    assert len(triage_results) == 1
    assert "IsoMalloc" in triage_results[0].affected_subsystems
    assert dispatcher.get_queue_depths()["native"] == 0

    ai_sentinel = Saga1MlSentinel()
    ai_advisories = dispatcher.drain_domain(BountyDomain.DOMAIN_AI)
    assert len(ai_advisories) == 1
    sentinel_results = ai_sentinel.process_advisories(ai_advisories)
    assert len(sentinel_results) == 1
    assert sentinel_results[0].taint_level == "CORTEX-TAINT"
    assert sentinel_results[0].vulnerability_class == Saga1VulnerabilityClass.UNSAFE_DESERIALIZATION
    assert dispatcher.get_queue_depths()["ai"] == 0


@pytest.mark.asyncio
async def test_live_network_ingestion_resilience() -> None:
    """Verifica el comportamiento no bloqueante con cliente HTTP real/mock."""
    transducer = BountyFeedTransducer()
    dispatcher = BountyRingDispatcher()

    # Ejecuta sondeo real con timeout acotado
    async with httpx.AsyncClient(timeout=5.0) as client:
        frames = await transducer.poll_live_network(client, per_page=3)

    # En caso de éxito de red, despacha las tramas capturadas
    for f in frames:
        dispatcher.dispatch_frame(f)

    # Verifica que el bucle no haya crasheado y las métricas sean coherentes
    telemetry = dispatcher.telemetry
    assert telemetry.total_corrupted_dropped == 0
    assert telemetry.total_dispatched == len(frames)
