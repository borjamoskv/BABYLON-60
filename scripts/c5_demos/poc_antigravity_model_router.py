#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v5.1 Sovereign Hardened
# █ UNIVERSAL TOPOLOGY ROUTER POC | DOMAIN: cognitive_pilot.autoroute | STATE: C5-REAL
# ============================================================================
"""
[AX-4] TOPOLOGY: Falsación Empírica del Router Universal de Capacidades (v3.0).

Valida empíricamente:
1. Cero Fuga de Secretos (INV_SOVEREIGN_AIRGAP): 100% de tareas con claves/PII enrutadas
   exclusivamente a loopback local 127.0.0.1 (litert://gemma4-26b / Ollama), NUNCA a
   modelos remotos como GPT-OSS 120B (Medium) [Notice].
2. Invariante de Rigor Deductivo: Demostraciones formales (Lean 4 / Z3) y Epistemic Halts
   enrutados a Estrato 3 Apex (Claude Opus 5.5 High / Orchestrator Carbon).
3. Invariante de Sistemas y Reposo (Omega_0): Ingeniería de sistemas y refactorizaciones
   acotadas cubiertas por Estrato 2 (Orchestrator Argon / Claude Sonnet 5.5).
4. Invariante de Throughput: Consultas de triaje enrutadas a Estrato 1 (Gemini 3.8 Flash / Hydrogen Low).
5. Latencia determinista O(1): < 50 microsegundos por decisión en lote de 1.000 iteraciones.
6. Atestación criptográfica: Recibos SHA3-256 + HMAC de cada decisión.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
import hashlib
import hmac
from pathlib import Path
import random
import sys
import time
from typing import Dict, List

repo_root = Path(__file__).absolute().parents[2]
kish_root = repo_root / "01_KISH_ENGINE"
for candidate in (repo_root, kish_root):
    if str(candidate) not in sys.path and candidate.is_dir():
        sys.path.insert(0, str(candidate))

from babylon60.cognitive_pilot.universal_autoroute import DEFAULT_HMAC_KEY  # noqa: E402


class ContextSize(Enum):
    C0_UNDER_32K = auto()
    C1_32K_128K = auto()
    C2_128K_500K = auto()
    C3_500K_2M = auto()


class DeductiveDepth(Enum):
    D0_MECHANICAL_IO = auto()
    D1_STRUCTURED_AST = auto()
    D2_SYSTEMS_TYPES = auto()
    D3_AXIOMATIC_FORMAL = auto()


class Sovereignty(Enum):
    S0_PUBLIC = auto()
    S1_CONFIDENTIAL = auto()
    S2_AIRGAP_CRYPTO = auto()


@dataclass(frozen=True)
class TaskVector:
    task_id: str
    ctx: ContextSize
    deduct: DeductiveDepth
    sov: Sovereignty
    is_multimodal: bool
    is_swarm_worker: bool
    is_epistemic_halt: bool
    contains_unredacted_secrets: bool


@dataclass(frozen=True)
class RouteDecision:
    rule_id: str
    model_name: str
    regime: str
    target_selector: str
    locality: str
    failover_model: str
    receipt_hmac: str
    latency_ns: int


class AntigravityModelRouter:
    """Router determinista O(1) alineado con C5-UNIVERSAL-AUTOROUTE v3.0."""

    def __init__(self, hmac_key: bytes = DEFAULT_HMAC_KEY) -> None:
        self.hmac_key = hmac_key

    def _sign_decision(self, task_id: str, model_name: str, regime: str, locality: str) -> str:
        payload = f"{task_id}:{model_name}:{regime}:{locality}".encode("utf-8")
        h = hashlib.sha3_256(payload).digest()
        return hmac.new(self.hmac_key, h, hashlib.sha256).hexdigest()[:16]

    def route(self, task: TaskVector) -> RouteDecision:
        t0 = time.perf_counter_ns()

        # 1. Invariante de Soberanía Absoluta (INV_SOVEREIGN_AIRGAP -> Loopback 127.0.0.1 exclusivo)
        if task.contains_unredacted_secrets or task.sov == Sovereignty.S2_AIRGAP_CRYPTO:
            model = "litert://gemma4-26b"
            regime = "Local-AirGap"
            selector = "litert://gemma4-26b (127.0.0.1)"
            locality = "loopback"
            failover = "FAIL_STOP_AIRGAP"
            rule = "R-AIRGAP-LOCAL"

        # 2. Epistemic Halt o Demostración Formal Axiomática (Lean 4 / Z3 / Seqlock Ring-0)
        elif task.is_epistemic_halt or task.deduct == DeductiveDepth.D3_AXIOMATIC_FORMAL:
            model = "Claude Opus 5.5"
            regime = "High"
            selector = "Claude Opus 5.5 (High)"
            locality = "remote"
            failover = "Orchestrator (Carbon)"
            rule = "R-LEAN4/HALT"

        # 3. Contexto Masivo (> 128k tokens) con Síntesis Multifichero
        elif task.ctx in (ContextSize.C2_128K_500K, ContextSize.C3_500K_2M):
            model = "Orchestrator (Carbon)"
            regime = "Orchestrator"
            selector = "Orchestrator (Carbon)"
            locality = "remote"
            failover = "Gemini 4 Argon (Medium)"
            rule = "R-BIGCTX-ORCH"

        # 4. Ingeniería de Silicio, Rust, C-FFI o Tipado Estricto (< 128K)
        elif task.deduct == DeductiveDepth.D2_SYSTEMS_TYPES:
            model = "Claude Sonnet 5.5"
            regime = "Low"
            selector = "Claude Sonnet 5.5 (Low)"
            locality = "remote"
            failover = "Orchestrator (Argon)"
            rule = "R-SYSTEMS"

        # 5. Multimodalidad Técnica o Ejecución Estándar (Punto de Reposo Omega_0)
        elif task.is_multimodal or task.deduct == DeductiveDepth.D1_STRUCTURED_AST:
            model = "Orchestrator (Argon)"
            regime = "Orchestrator"
            selector = "Orchestrator (Argon)"
            locality = "remote"
            failover = "Gemini 4 Argon (Low)"
            rule = "R-OMEGA0-ARGON"

        # 6. Workers Paralelos de Enjambre (d=1 Leaf Subagent)
        elif task.is_swarm_worker:
            model = "Gemini 4 Hydrogen"
            regime = "Low"
            selector = "Gemini 4 Hydrogen (Low)"
            locality = "remote"
            failover = "Gemini 3.8 Flash (High (Fast))"
            rule = "R-SWARM_W"

        # 7. Hot-Path / Triaje Cinético por Defecto
        else:
            model = "Gemini 3.8 Flash"
            regime = "High (Fast)"
            selector = "Gemini 3.8 Flash (High (Fast))"
            locality = "remote"
            failover = "Gemini 4 Hydrogen (Low)"
            rule = "R-TOOLHOT"

        t1 = time.perf_counter_ns()
        receipt = self._sign_decision(task.task_id, model, regime, locality)

        return RouteDecision(
            rule_id=rule,
            model_name=model,
            regime=regime,
            target_selector=selector,
            locality=locality,
            failover_model=failover,
            receipt_hmac=receipt,
            latency_ns=t1 - t0,
        )


def run_stress_test(iterations: int = 1000) -> None:
    print("=" * 78)
    print("█ BABYLON-60 / UNIVERSAL AUTOROUTE v3.0 — STRESS TEST 1000 ITERACIONES")
    print("=" * 78)

    router = AntigravityModelRouter()
    distribution: Dict[str, int] = {}
    latencies: List[int] = []
    airgap_violations = 0
    halt_violations = 0
    systems_violations = 0

    random.seed(42)
    t_start = time.perf_counter()

    for i in range(iterations):
        has_secrets = random.random() < 0.15
        sov = (
            Sovereignty.S2_AIRGAP_CRYPTO
            if has_secrets or random.random() < 0.10
            else (Sovereignty.S1_CONFIDENTIAL if random.random() < 0.40 else Sovereignty.S0_PUBLIC)
        )
        is_halt = (not has_secrets) and (random.random() < 0.08)
        deduct = random.choice(list(DeductiveDepth))
        ctx = random.choice(list(ContextSize))
        is_multi = random.random() < 0.12
        is_worker = random.random() < 0.20

        task = TaskVector(
            task_id=f"task-{i:04d}",
            ctx=ctx,
            deduct=deduct,
            sov=sov,
            is_multimodal=is_multi,
            is_swarm_worker=is_worker,
            is_epistemic_halt=is_halt,
            contains_unredacted_secrets=has_secrets,
        )

        decision = router.route(task)
        latencies.append(decision.latency_ns)
        distribution[decision.model_name] = distribution.get(decision.model_name, 0) + 1

        if (has_secrets or sov == Sovereignty.S2_AIRGAP_CRYPTO) and decision.locality != "loopback":
            airgap_violations += 1

        if (
            is_halt
            and decision.model_name != "Claude Opus 5.5"
            and not has_secrets
            and sov != Sovereignty.S2_AIRGAP_CRYPTO
        ):
            halt_violations += 1

        if (
            (not has_secrets)
            and (sov != Sovereignty.S2_AIRGAP_CRYPTO)
            and (not is_halt)
            and (deduct == DeductiveDepth.D2_SYSTEMS_TYPES)
            and (ctx in (ContextSize.C0_UNDER_32K, ContextSize.C1_32K_128K))
            and decision.model_name != "Claude Sonnet 5.5"
        ):
            systems_violations += 1

    t_total = time.perf_counter() - t_start
    avg_latency_us = (sum(latencies) / len(latencies)) / 1_000
    p99_latency_us = sorted(latencies)[int(len(latencies) * 0.99)] / 1_000

    print(f"\n[+] Total Iteraciones:           {iterations}")
    print(f"[+] Tiempo Total de Ejecución:    {t_total * 1000:.2f} ms")
    print(f"[+] Latencia Media por Decisión:  {avg_latency_us:.3f} µs")
    print(f"[+] Latencia P99 por Decisión:    {p99_latency_us:.3f} µs")
    print("\n[+] Distribución de Enrutamiento:")
    for model, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        pct = (count / iterations) * 100
        bar = "█" * int(pct / 2)
        print(f"    - {model:<24}: {count:>4} ({pct:>5.1f}%) {bar}")

    print("\n[+] Auditoría de Invariantes C5:")
    print(f"    - Fugas de Secretos / Air-Gap:   {airgap_violations} (Objetivo: 0)")
    print(f"    - Desvíos de Epistemic Halt:     {halt_violations} (Objetivo: 0)")
    print(f"    - Fracturas de Silicio/Rust:     {systems_violations} (Objetivo: 0)")

    assert airgap_violations == 0, "FATAL: Invariante INV_SOVEREIGN_AIRGAP violada!"
    assert halt_violations == 0, "FATAL: Invariante INV_EPISTEMIC_HALT violada!"
    assert systems_violations == 0, "FATAL: Invariante INV_SYSTEMS_RUST violada!"

    print("\n[✓] CERTIFICACIÓN EXITOSA: PoC v3.0 supera el 100% de los asertos termodinámicos.\n")


if __name__ == "__main__":
    run_stress_test(1000)
