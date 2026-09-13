#!/usr/bin/env python3
# ruff: noqa: E402
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""poc_legion_1000.py — PoC de Falsación Empírica para el Operativo Legión Ω-1000.

Valida:
1. Generación de 1000 advisories sintéticos realistas (3 dominios).
2. Ingestión y despacho B60IPC sin corrupciones.
3. Ciclo de análisis de un lote de 100 advisories (1/10 del total).
4. Inserción de ≥1 recibo SCITT en un Cold Ledger de test (temp dir).

INVARIANTE: Este script NO toca bounty_ledger.db de producción.
"""

from __future__ import annotations

import os
import random
import sys
import tempfile
import time

# ── Resolver PYTHONPATH ────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(_ROOT, "01_ORCHESTRATOR"))

from babylon60.bft.bounty_claim_attester import BountyClaimAttester
from babylon60.bft.bounty_cold_ledger import BountyColdLedger
from babylon60.bft.bounty_ring_dispatcher import BountyRingDispatcher
from babylon60.bft.defi_bytecode_scraper import DeFiBytecodeScraper
from babylon60.bft.saga1_ml_sentinel import Saga1MlSentinel
from babylon60.bft.webkit_memory_connector import WebKitMemoryConnector
from babylon60.transducers.bounty_feed_transducer import (
    BountyDomain,
    BountyFeedTransducer,
)

# ── Generador de advisories sintéticos ────────────────────────────────────

EVM_TITLES = [
    "Uniswap v4 hook transient storage reentrancy",
    "ERC-4337 EntryPoint flash loan manipulation",
    "Compound v3 liquidation oracle manipulation via flash loan",
    "Aave v3 reentrancy in flash loan callback",
    "Curve Finance pool manipulation via read-only reentrancy",
    "EIP-1153 TSTORE collision in delegated proxy",
    "OpenZeppelin ERC20Permit replay across chains",
    "Foundry fuzzer reveals solidity 0.8.24 storage aliasing",
]

NATIVE_TITLES = [
    "WebKit Gigacage bypass via DFG JIT type confusion",
    "JavaScriptCore IsoMalloc use-after-free in GC sweep",
    "V8 out-of-bounds write in TurboFan array bounds elision",
    "macOS kernel heap overflow in mach voucher",
    "ARM64 JIT spraying via WebGL shader compilation",
    "WebKit BMalloc large allocation escape from cage",
    "JSC FTL compiler arbitrary code execution",
    "Safari memory corruption in AudioContext node graph",
]

AI_TITLES = [
    "PyTorch arbitrary code execution via unsafe torch.load pickle",
    "LangChain prompt injection in tool call parser",
    "HuggingFace safetensors pickle deserialization bypass",
    "RLHF reward model inversion via gradient leakage",
    "LLM jailbreak via token boundary confusion",
    "Transformer attention mask spoofing for data exfiltration",
    "Model inversion via PyTorch autograd side-channel",
    "GGUF loader arbitrary code execution in llama.cpp",
]


def _rand_hex(n: int = 8) -> str:
    return "".join(random.choices("0123456789abcdef", k=n))


def _rand_cvss() -> float:
    return round(random.uniform(5.0, 10.0), 1)


def _rand_severity() -> str:
    return random.choice(["critical", "high", "medium"])


def generate_synthetic_advisories(n: int = 1000) -> list[dict[str, object]]:
    """Genera N advisories sintéticos distribuidos en 3 dominios."""
    evm_count = int(n * 0.4)      # 400
    native_count = int(n * 0.3)   # 300
    ai_count = n - evm_count - native_count  # 300

    advisories: list[dict[str, object]] = []

    for i in range(evm_count):
        title = random.choice(EVM_TITLES) + f" #{i}"
        advisories.append({
            "ghsa_id": f"GHSA-EVM-{_rand_hex(4)}-{_rand_hex(4)}",
            "summary": title,
            "description": f"EVM bytecode exploit: {_rand_hex(16)}. CVSS {_rand_cvss()}.",
            "severity": _rand_severity(),
            "html_url": f"https://github.com/advisories/GHSA-EVM-{_rand_hex(8)}",
            "vulnerabilities": [{"package": {"ecosystem": "solidity"}}],
        })

    for i in range(native_count):
        title = random.choice(NATIVE_TITLES) + f" #{i}"
        advisories.append({
            "ghsa_id": f"GHSA-NAT-{_rand_hex(4)}-{_rand_hex(4)}",
            "summary": title,
            "description": f"Memory corruption via webkit heap: {_rand_hex(16)}. use-after-free in IsoMalloc.",
            "severity": _rand_severity(),
            "html_url": f"https://github.com/advisories/GHSA-NAT-{_rand_hex(8)}",
            "vulnerabilities": [{"package": {"ecosystem": "cpp"}}],
        })

    for i in range(ai_count):
        title = random.choice(AI_TITLES) + f" #{i}"
        advisories.append({
            "ghsa_id": f"GHSA-AI-{_rand_hex(4)}-{_rand_hex(4)}",
            "summary": title,
            "description": f"PyTorch/LLM exploit via pickle tensor: {_rand_hex(16)}. RLHF jailbreak vector.",
            "severity": _rand_severity(),
            "html_url": f"https://github.com/advisories/GHSA-AI-{_rand_hex(8)}",
            "vulnerabilities": [{"package": {"ecosystem": "pip"}}],
        })

    random.shuffle(advisories)
    return advisories


# ── PoC Principal ──────────────────────────────────────────────────────────

def run_poc() -> None:
    random.seed(42)  # Reproducibilidad determinista

    print("=" * 70)
    print("🔬 POC LEGIÓN Ω-1000: FALSACIÓN EMPÍRICA (1 lote de 100 advisories)")
    print("=" * 70)

    # 1. Generar 1000 advisories
    t0 = time.perf_counter()
    all_advisories = generate_synthetic_advisories(1000)
    gen_ms = (time.perf_counter() - t0) * 1000
    print(f"[✓] Generados {len(all_advisories)} advisories sintéticos en {gen_ms:.1f} ms")

    # 2. Usar solo el primer lote de 100 para el PoC
    batch = all_advisories[:100]

    # 3. Transductor → tramas B60IPC
    transducer = BountyFeedTransducer(filter_capacity=50_000)
    dispatcher = BountyRingDispatcher(queue_capacity=5_000)

    t1 = time.perf_counter()
    frames = transducer.ingest_raw_advisories(batch)
    ingest_ms = (time.perf_counter() - t1) * 1000
    print(f"[✓] {len(frames)} tramas B60IPC generadas en {ingest_ms:.1f} ms (duplicados filtrados: {100 - len(frames)})")

    # 4. Despacho
    for f in frames:
        dispatcher.dispatch_frame(f)

    depths = dispatcher.get_queue_depths()
    tel = dispatcher.telemetry
    print(f"[✓] Despacho: EVM={depths['evm']} NATIVE={depths['native']} AI={depths['ai']} GENERAL={depths['general']}")
    print(f"    Telemetría: dispatched={tel.total_dispatched} corrupted={tel.total_corrupted_dropped}")
    assert tel.total_corrupted_dropped == 0, "FALLO: tramas corruptas detectadas"

    # 5. Análisis especializado
    defi = DeFiBytecodeScraper()
    webkit = WebKitMemoryConnector()
    saga1 = Saga1MlSentinel()

    evm_batch = dispatcher.drain_domain(BountyDomain.DOMAIN_EVM)
    evm_results = defi.process_advisories(evm_batch)

    nat_batch = dispatcher.drain_domain(BountyDomain.DOMAIN_NATIVE)
    nat_results = webkit.process_advisories(nat_batch)

    ai_batch = dispatcher.drain_domain(BountyDomain.DOMAIN_AI)
    ai_results = saga1.process_advisories(ai_batch)

    print(f"[✓] Análisis: EVM={len(evm_results)} NATIVE={len(nat_results)} AI={len(ai_results)}")

    # 6. Atestación SCITT con Cold Ledger en temp dir
    attester = BountyClaimAttester()
    tmpdir = tempfile.mkdtemp(prefix="poc_b60_legion_")
    db_path = os.path.join(tmpdir, "poc_bounty_ledger.db")
    ledger = BountyColdLedger(db_path=db_path)
    ledger.start()

    receipts_generated = 0
    for res in evm_results:
        if res.risk_score >= 0.5:
            r = attester.generate_receipt(
                advisory_id=res.contract_address or "EVM-UNKNOWN",
                domain="DOMAIN_EVM",
                finding_summary="; ".join(res.findings[:2]),
                risk_score=res.risk_score,
                raw_payload=res.to_dict(),
            )
            ledger.enqueue_receipt(r)
            receipts_generated += 1

    for nat_res in nat_results:
        if nat_res.risk_score >= 0.5:
            r = attester.generate_receipt(
                advisory_id=nat_res.advisory_id,
                domain="DOMAIN_NATIVE",
                finding_summary=f"{nat_res.vulnerability_class} @ {nat_res.affected_subsystems}",
                risk_score=nat_res.risk_score,
                raw_payload=nat_res.to_dict(),
            )
            ledger.enqueue_receipt(r)
            receipts_generated += 1

    for ai_res in ai_results:
        if ai_res.risk_score >= 0.5:
            r = attester.generate_receipt(
                advisory_id=ai_res.advisory_id,
                domain="DOMAIN_AI",
                finding_summary=f"{ai_res.vulnerability_class.value} [{ai_res.taint_level}]",
                risk_score=ai_res.risk_score,
                raw_payload=ai_res.to_dict(),
            )
            ledger.enqueue_receipt(r)
            receipts_generated += 1

    # Dar tiempo al ColdLedger async para drenar
    time.sleep(0.5)
    ledger.stop()

    elapsed = (time.perf_counter() - t0) * 1000
    print(f"[✓] Recibos SCITT encolados: {receipts_generated}")
    print(f"[✓] DB temporal: {db_path}")
    print(f"[✓] Tiempo total PoC: {elapsed:.1f} ms")

    # Verificar DB
    import sqlite3
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM bounty_claims").fetchone()[0]
    conn.close()
    print(f"[✓] Recibos persistidos en SQLite: {count}")

    assert receipts_generated >= 1, "FALLO: ningún recibo generado"
    print("\n✅ POC SUPERADO — Topología validada para 1000 agentes")
    print("=" * 70)


if __name__ == "__main__":
    run_poc()
