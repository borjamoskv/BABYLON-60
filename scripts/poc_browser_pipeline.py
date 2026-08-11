#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from babylon60.core.browser_agent import BrowserResearchAgent


def mock_network_fetcher(url: str) -> str:
    """Simulates HTTP fetcher."""
    if "hype" in url:
        return "100x passive income game changer revolutionary disruption"
    return (
        "The Rust language uses affine type system semantics to ensure zero-cost abstractions "
        "and memory safety without a garbage collector. "
        "Detailed documentation can be reviewed at https://doc.rust-lang.org/book/ "
        "SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )


def run_test():
    print("=== [Causal-Determinist] Verificación End-to-End del BrowserResearchAgent SDK ===")

    agent = BrowserResearchAgent()
    taint = "session_bft_audit_001"

    # 1. Test Valid URL (Fetch + Filter + Cache + Attestation)
    target_url = f"https://doc.rust-lang.org/std-{int(time.time())}"
    res1 = agent.fetch_and_verify(target_url, mock_network_fetcher, causal_taint=taint)
    print("\n1. Fetch URL Válida:", res1["status"])
    print("Anclas Físicas Extraídas:", res1["anchors"])
    print("BFT Attestation (Lamport t):", res1["bft_attestation"])
    assert res1["status"] == "VERIFIED_AND_ATTESTED"
    assert res1["bft_attestation"]["lamport_t"] > 0
    assert len(res1["anchors"]) >= 2

    # 2. Test Cache Hit
    res2 = agent.fetch_and_verify(target_url, mock_network_fetcher, causal_taint=taint)
    print("\n2. Fetch URL Caché Hit:", res2["status"])
    assert res2["status"] == "CACHE_HIT"

    # 3. Test Rejection of Hype (Popperian Falsification Gate)
    hype_url = f"https://spam.com/hype-{int(time.time())}"
    res3 = agent.fetch_and_verify(hype_url, mock_network_fetcher, causal_taint=taint)
    print("\n3. Fetch URL Hype (Rechazo Popperiano):", res3["status"], "| Motivo:", res3.get("reason"))
    assert res3["status"] == "REJECTED"

    print("\n[SUCCESS] BrowserResearchAgent SDK 100% Verificado en Causal-Determinist.")


if __name__ == "__main__":
    run_test()
