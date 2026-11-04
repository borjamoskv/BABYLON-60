#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ BABYLON-21 CONSOLIDATION TOPOLOGY | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
Babylon-21 Consolidation Swarm Topology (3x7 Triadic Matrix).

Implements the 21 specialized consolidation agents governing BABYLON-60 across:
  - Squad I   (AG-01..AG-07): Ring-0 & Formal Verification (00_ABZU_KERNEL, src/, crates/)
  - Squad II  (AG-08..AG-14): Ring-1/2 KISH Engine & C-ABI/MCP Bridges (01_KISH_ENGINE)
  - Squad III (AG-15..AG-21): Ring-2/3/4 EDIN Swarms, Governance & Apex BFT Seal (02_EDIN_SWARMS)

Enforces:
  - MASS Stage 1 & 2 (RULE[circuit_topology_optimization]): Independent causal utility &
    disjoint write partitions per agent before topological DAG composition.
  - Deterministic Causal Hashing (INV_C5_CANONICAL_LOGICAL_TICK): State digests and
    Merkle leaves depend exclusively on injected `logical_tick`.
  - Markov Blanket Projection (Delta I <= 0): Bounded local state per agent transition.
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Dict, List, Mapping, Sequence, Tuple


def _canonical_blake3_hex(payload: bytes) -> str:
    """Computes canonical 256-bit digest using BLAKE3 (or SHA-256 fallback if C-ext absent)."""
    try:
        import blake3

        return str(blake3.blake3(payload).hexdigest())
    except ImportError:  # pragma: no cover
        return hashlib.sha256(b"BLAKE3_DOMAIN_FALLBACK:" + payload).hexdigest()


class ConsolidationSquad(Enum):
    """Three 7-agent squads forming the 21-agent BABYLON-60 consolidation matrix."""

    SQUAD_I_ABZU_RING0 = "squad_1_abzu_ring0"
    SQUAD_II_KISH_ENGINE = "squad_2_kish_engine"
    SQUAD_III_EDIN_GATES = "squad_3_edin_gates"


class ArchitecturalRing(Enum):
    """Canonical C5-REAL architectural rings."""

    RING_0_SILICON = "RING-0"
    RING_1_FORMAL = "RING-1"
    RING_2_SWARM = "RING-2"
    RING_3_BOUNDARY = "RING-3"
    RING_4_GOVERNANCE = "RING-4"


class ConsolidationAgentId(Enum):
    """Canonical identifiers for the 21 BABYLON-60 consolidation agents."""

    AG_01 = "AG-01"
    AG_02 = "AG-02"
    AG_03 = "AG-03"
    AG_04 = "AG-04"
    AG_05 = "AG-05"
    AG_06 = "AG-06"
    AG_07 = "AG-07"
    AG_08 = "AG-08"
    AG_09 = "AG-09"
    AG_10 = "AG-10"
    AG_11 = "AG-11"
    AG_12 = "AG-12"
    AG_13 = "AG-13"
    AG_14 = "AG-14"
    AG_15 = "AG-15"
    AG_16 = "AG-16"
    AG_17 = "AG-17"
    AG_18 = "AG-18"
    AG_19 = "AG-19"
    AG_20 = "AG-20"
    AG_21 = "AG-21"


@dataclass(frozen=True)
class ConsolidationAgentSpec:
    """Immutable specification of a single consolidation agent (MASS Stage 1 block)."""

    agent_id: ConsolidationAgentId
    canonical_name: str
    squad: ConsolidationSquad
    ring: ArchitecturalRing
    target_paths: Tuple[str, ...]
    invariant_id: str
    gate_command: str
    causal_dependencies: Tuple[ConsolidationAgentId, ...]


@dataclass(frozen=True)
class AgentGateOutcome:
    """Deterministic outcome record emitted by a consolidation agent at a logical tick."""

    agent_id: ConsolidationAgentId
    canonical_name: str
    verified: bool
    logical_tick: int
    evidence_digest: str
    detail: str

    def leaf_digest(self) -> str:
        """Computes canonical Merkle leaf digest strictly from causal fields (INV_C5_CANONICAL_LOGICAL_TICK)."""
        status_flag = "PASS" if self.verified else "FAIL"
        raw = (
            f"B60_AGENT_LEAF|v1|{self.agent_id.value}|{self.canonical_name}|"
            f"{status_flag}|tick={self.logical_tick}|{self.evidence_digest}"
        ).encode("utf-8")
        return _canonical_blake3_hex(raw)


@dataclass(frozen=True)
class ConsolidationSealReceipt:
    """Immutable BFT consolidation seal produced by AG-21 across all 21 agents."""

    logical_tick: int
    total_agents: int
    verified_count: int
    failed_agents: Tuple[str, ...]
    squad_digests: Mapping[str, str]
    merkle_root_hex: str
    consolidated: bool
    outcomes: Tuple[AgentGateOutcome, ...]


BABYLON21_AGENTS: Tuple[ConsolidationAgentSpec, ...] = (
    # ------------------------------------------------------------------------
    # SQUAD I: Ring-0 Silicon, ABZU Kernel & Formal Verification (AG-01..AG-07)
    # ------------------------------------------------------------------------
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_01,
        canonical_name="ring0_manifest_seqlock",
        squad=ConsolidationSquad.SQUAD_I_ABZU_RING0,
        ring=ArchitecturalRing.RING_0_SILICON,
        target_paths=("src/manifest.rs", "src/seqlock.rs", "src/spsc_ring.rs"),
        invariant_id="INV_C5_SPSC_UNSAFE_CELL",
        gate_command="cargo test -q --lib seqlock",
        causal_dependencies=(),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_02,
        canonical_name="ring0_secure_fs_nemesis",
        squad=ConsolidationSquad.SQUAD_I_ABZU_RING0,
        ring=ArchitecturalRing.RING_0_SILICON,
        target_paths=("src/secure_fs.rs", "tests/nemesis_wave4.rs"),
        invariant_id="INV_C5_NEMESIS_EVIDENCE_CONTRACT",
        gate_command="cargo test -q --test nemesis_wave4",
        causal_dependencies=(),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_03,
        canonical_name="ring0_enclave_attest",
        squad=ConsolidationSquad.SQUAD_I_ABZU_RING0,
        ring=ArchitecturalRing.RING_0_SILICON,
        target_paths=("src/enclave.rs", "src/attestation_contract.rs", "crates/babylon-attest"),
        invariant_id="INV_C5_SECURE_ENCLAVE_POINT_NORMALIZATION",
        gate_command="cargo test -q --lib enclave",
        causal_dependencies=(),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_04,
        canonical_name="ring0_larsa_bft_wal",
        squad=ConsolidationSquad.SQUAD_I_ABZU_RING0,
        ring=ArchitecturalRing.RING_0_SILICON,
        target_paths=("src/larsa_bft.rs", "src/worm.rs", "src/receipt.rs"),
        invariant_id="INV_C5_WAL_SYNCHRONOUS_FULL",
        gate_command="cargo test -q --lib larsa",
        causal_dependencies=(),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_05,
        canonical_name="ring0_dec_f60_thermo",
        squad=ConsolidationSquad.SQUAD_I_ABZU_RING0,
        ring=ArchitecturalRing.RING_0_SILICON,
        target_paths=("src/dec.rs", "src/f60.rs", "src/thermodynamics.rs"),
        invariant_id="INV_C5_DEC_MIMETIC",
        gate_command="cargo test -q --lib dec",
        causal_dependencies=(),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_06,
        canonical_name="ring1_z3_lean4_oracle",
        squad=ConsolidationSquad.SQUAD_I_ABZU_RING0,
        ring=ArchitecturalRing.RING_1_FORMAL,
        target_paths=("src/z3_oracle.rs", "src/aot_oracle.rs", "src/lean_emitter.rs"),
        invariant_id="INV_C5_Z3_SMT_PRE_LEAN",
        gate_command="cargo test -q --lib z3_oracle",
        causal_dependencies=(),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_07,
        canonical_name="ring0_subcrates_parity",
        squad=ConsolidationSquad.SQUAD_I_ABZU_RING0,
        ring=ArchitecturalRing.RING_0_SILICON,
        target_paths=("00_ABZU_KERNEL/crates", "crates/b60-lang", "crates/cadt_mediator", "crates/eridu-infer"),
        invariant_id="INV_C5_LICENSE_PARITY_GATE",
        gate_command="cargo check --workspace --locked -q",
        causal_dependencies=(
            ConsolidationAgentId.AG_01,
            ConsolidationAgentId.AG_02,
            ConsolidationAgentId.AG_03,
            ConsolidationAgentId.AG_04,
            ConsolidationAgentId.AG_05,
            ConsolidationAgentId.AG_06,
        ),
    ),
    # ------------------------------------------------------------------------
    # SQUAD II: Ring-1 & Ring-2 KISH Engine & C-ABI/MCP Bridges (AG-08..AG-14)
    # ------------------------------------------------------------------------
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_08,
        canonical_name="kish_kernel_ffi_bridge",
        squad=ConsolidationSquad.SQUAD_II_KISH_ENGINE,
        ring=ArchitecturalRing.RING_1_FORMAL,
        target_paths=("01_KISH_ENGINE/babylon60/kernel", "src/ffi_python.rs"),
        invariant_id="INV_C5_MMAP_AFFINE_ANNIHILATION",
        gate_command="uv run --no-sync pytest 01_KISH_ENGINE -k kernel -q",
        causal_dependencies=(ConsolidationAgentId.AG_01,),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_09,
        canonical_name="kish_bft_persistence",
        squad=ConsolidationSquad.SQUAD_II_KISH_ENGINE,
        ring=ArchitecturalRing.RING_1_FORMAL,
        target_paths=(
            "01_KISH_ENGINE/babylon60/bft",
            "01_KISH_ENGINE/babylon60/crypto",
            "01_KISH_ENGINE/babylon60/persistence",
        ),
        invariant_id="INV_C5_DAG_EVENT_ID",
        gate_command="uv run --no-sync pytest tests/test_cortex_crypto_kernel.py -q",
        causal_dependencies=(ConsolidationAgentId.AG_04,),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_10,
        canonical_name="kish_mcp_ephemeral_bomb",
        squad=ConsolidationSquad.SQUAD_II_KISH_ENGINE,
        ring=ArchitecturalRing.RING_2_SWARM,
        target_paths=(
            "01_KISH_ENGINE/babylon60/mcp",
            "01_KISH_ENGINE/babylon60/cli",
            "01_KISH_ENGINE/babylon60/agents/sovereign_mcp",
        ),
        invariant_id="INV_C5_MCP_EPHEMERAL_BOMB",
        gate_command="uv run --no-sync pytest tests/test_cortex_mcp_server.py -q",
        causal_dependencies=(ConsolidationAgentId.AG_06,),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_11,
        canonical_name="kish_verifier_acs_bridge",
        squad=ConsolidationSquad.SQUAD_II_KISH_ENGINE,
        ring=ArchitecturalRing.RING_2_SWARM,
        target_paths=(
            "src/acs_bridge.rs",
            "01_KISH_ENGINE/babylon60/verification",
            "01_KISH_ENGINE/babylon60/compliance_exporter",
        ),
        invariant_id="INV_C5_OWASP_ACS_BRIDGE",
        gate_command="cargo test -q --lib acs_bridge",
        causal_dependencies=(ConsolidationAgentId.AG_03,),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_12,
        canonical_name="kish_cortex_transducers",
        squad=ConsolidationSquad.SQUAD_II_KISH_ENGINE,
        ring=ArchitecturalRing.RING_1_FORMAL,
        target_paths=(
            "01_KISH_ENGINE/babylon60/cortex",
            "01_KISH_ENGINE/babylon60/transducers",
            "01_KISH_ENGINE/babylon60/autodidact",
        ),
        invariant_id="INV_C5_BEKENSTEIN_LANDAUER_APOPTOSIS",
        gate_command="uv run --no-sync pytest tests/test_cortex_bpe_tokenizer.py tests/test_appgen_ast_transducer.py -q",
        causal_dependencies=(ConsolidationAgentId.AG_05,),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_13,
        canonical_name="kish_canonical_ontology",
        squad=ConsolidationSquad.SQUAD_II_KISH_ENGINE,
        ring=ArchitecturalRing.RING_1_FORMAL,
        target_paths=("src/ontology.rs", "01_KISH_ENGINE/babylon60/primitives"),
        invariant_id="INV_C5_PARASITIC_DOF_QUOTIENT",
        gate_command="cargo test -q --lib ontology",
        causal_dependencies=(ConsolidationAgentId.AG_04,),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_14,
        canonical_name="kish_static_typing_gate",
        squad=ConsolidationSquad.SQUAD_II_KISH_ENGINE,
        ring=ArchitecturalRing.RING_2_SWARM,
        target_paths=("01_KISH_ENGINE/babylon60/__init__.py",),
        invariant_id="INV_C5_ZERO_DEBT_LINTER",
        gate_command="uv run --no-sync ruff check 01_KISH_ENGINE 02_EDIN_SWARMS",
        causal_dependencies=(
            ConsolidationAgentId.AG_08,
            ConsolidationAgentId.AG_09,
            ConsolidationAgentId.AG_10,
            ConsolidationAgentId.AG_11,
            ConsolidationAgentId.AG_12,
            ConsolidationAgentId.AG_13,
        ),
    ),
    # ------------------------------------------------------------------------
    # SQUAD III: Ring-2/3/4 EDIN Swarms, Governance & Apex Seal (AG-15..AG-21)
    # ------------------------------------------------------------------------
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_15,
        canonical_name="edin_cta_orchestrator",
        squad=ConsolidationSquad.SQUAD_III_EDIN_GATES,
        ring=ArchitecturalRing.RING_2_SWARM,
        target_paths=(
            "02_EDIN_SWARMS/agents_archi/orchestrator/swarm.py",
            "02_EDIN_SWARMS/agents_archi/orchestrator/kda_dag_swarm.py",
            "02_EDIN_SWARMS/agents_archi/orchestrator/seqlock_swarm_ring0.py",
        ),
        invariant_id="INV_C5_CTA_MARKOV_PROJECTION",
        gate_command="uv run --no-sync pytest 02_EDIN_SWARMS/tests/test_lifecycle_resilience.py -q",
        causal_dependencies=(ConsolidationAgentId.AG_08,),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_16,
        canonical_name="edin_babylon21_topology",
        squad=ConsolidationSquad.SQUAD_III_EDIN_GATES,
        ring=ArchitecturalRing.RING_2_SWARM,
        target_paths=(
            "02_EDIN_SWARMS/agents_archi/topologies/babylon21_consolidation.py",
            "02_EDIN_SWARMS/agents_archi/topologies/router.py",
        ),
        invariant_id="INV_C5_EDIN_BARRIER",
        gate_command="uv run --no-sync pytest 02_EDIN_SWARMS/tests/test_babylon21_consolidation.py -q",
        causal_dependencies=(ConsolidationAgentId.AG_15,),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_17,
        canonical_name="edin_protocols_aof",
        squad=ConsolidationSquad.SQUAD_III_EDIN_GATES,
        ring=ArchitecturalRing.RING_2_SWARM,
        target_paths=(
            "02_EDIN_SWARMS/agents_archi/protocols/aof.py",
            "02_EDIN_SWARMS/agents_archi/protocols/attestation.py",
            "02_EDIN_SWARMS/agents_archi/protocols/bayesian_disintegration.py",
        ),
        invariant_id="INV_C5_BAYESIAN_DISINTEGRATION",
        gate_command="uv run --no-sync pytest 02_EDIN_SWARMS/tests -q",
        causal_dependencies=(ConsolidationAgentId.AG_15,),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_18,
        canonical_name="ring3_entropy_3strata",
        squad=ConsolidationSquad.SQUAD_III_EDIN_GATES,
        ring=ArchitecturalRing.RING_3_BOUNDARY,
        target_paths=("scripts/c5_quality_gates/audit_entropy_3strata.py",),
        invariant_id="INV_C5_ENTROPY_3STRATA_GATE",
        gate_command="python3 scripts/c5_quality_gates/audit_entropy_3strata.py",
        causal_dependencies=(ConsolidationAgentId.AG_07, ConsolidationAgentId.AG_14),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_19,
        canonical_name="ring3_docs_ghost_nodes",
        squad=ConsolidationSquad.SQUAD_III_EDIN_GATES,
        ring=ArchitecturalRing.RING_3_BOUNDARY,
        target_paths=("docs/00_index.md", "docs/SPECIFICATION.md"),
        invariant_id="INV_C5_GHOST_NODE_EXCLUSIONS",
        gate_command="python3 scripts/c5_quality_gates/detect_ghost_nodes.py",
        causal_dependencies=(ConsolidationAgentId.AG_07, ConsolidationAgentId.AG_14),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_20,
        canonical_name="ring4_ide_token_budget",
        squad=ConsolidationSquad.SQUAD_III_EDIN_GATES,
        ring=ArchitecturalRing.RING_4_GOVERNANCE,
        target_paths=(".babylon60rules", "AGENTS.md", "scripts/c5_quality_gates/audit_token_budget.py"),
        invariant_id="INV_C5_ARGON_GOVERNANCE",
        gate_command="python3 scripts/c5_quality_gates/audit_token_budget.py",
        causal_dependencies=(ConsolidationAgentId.AG_07, ConsolidationAgentId.AG_14),
    ),
    ConsolidationAgentSpec(
        agent_id=ConsolidationAgentId.AG_21,
        canonical_name="apex_bft_consolidation_seal",
        squad=ConsolidationSquad.SQUAD_III_EDIN_GATES,
        ring=ArchitecturalRing.RING_0_SILICON,
        target_paths=("RELEASE_MANIFEST.json",),
        invariant_id="INV_C5_CANONICAL_LOGICAL_TICK",
        gate_command="cargo test -q --test nemesis_wave4 && uv run --no-sync pytest 02_EDIN_SWARMS/tests -q",
        causal_dependencies=(
            ConsolidationAgentId.AG_01,
            ConsolidationAgentId.AG_02,
            ConsolidationAgentId.AG_03,
            ConsolidationAgentId.AG_04,
            ConsolidationAgentId.AG_05,
            ConsolidationAgentId.AG_06,
            ConsolidationAgentId.AG_07,
            ConsolidationAgentId.AG_08,
            ConsolidationAgentId.AG_09,
            ConsolidationAgentId.AG_10,
            ConsolidationAgentId.AG_11,
            ConsolidationAgentId.AG_12,
            ConsolidationAgentId.AG_13,
            ConsolidationAgentId.AG_14,
            ConsolidationAgentId.AG_15,
            ConsolidationAgentId.AG_16,
            ConsolidationAgentId.AG_17,
            ConsolidationAgentId.AG_18,
            ConsolidationAgentId.AG_19,
            ConsolidationAgentId.AG_20,
        ),
    ),
)

GateEvaluatorFn = Callable[
    [ConsolidationAgentSpec, int],
    bool | Tuple[bool, str] | Awaitable[bool | Tuple[bool, str]],
]


class Babylon21ConsolidationTopology:
    """
    Sovereign 21-Agent Consolidation Engine for BABYLON-60.

    Organizes the 21 agents into 3 squads of 7 agents each and executes them
    along their topological DAG waves with Markov-bounded context projection.
    """

    EXPECTED_AGENT_COUNT: int = 21
    SQUAD_SIZE: int = 7
    MAX_MARKOV_EVENTS: int = 8

    def __init__(
        self,
        agents: Sequence[ConsolidationAgentSpec] = BABYLON21_AGENTS,
        max_concurrency: int = 7,
    ) -> None:
        self._agents: Tuple[ConsolidationAgentSpec, ...] = tuple(agents)
        self._by_id: Dict[ConsolidationAgentId, ConsolidationAgentSpec] = {spec.agent_id: spec for spec in self._agents}
        self.max_concurrency: int = max(1, min(21, max_concurrency))
        self.verify_mass_stage1_invariants()

    @property
    def agents(self) -> Tuple[ConsolidationAgentSpec, ...]:
        """Returns the immutable tuple of 21 consolidation agent specs."""
        return self._agents

    def get_agent(self, agent_id: ConsolidationAgentId) -> ConsolidationAgentSpec:
        """Returns the specification for a specific consolidation agent."""
        return self._by_id[agent_id]

    def squad_agents(self, squad: ConsolidationSquad) -> Tuple[ConsolidationAgentSpec, ...]:
        """Returns the 7 agents belonging to the requested squad."""
        return tuple(spec for spec in self._agents if spec.squad == squad)

    def verify_mass_stage1_invariants(self) -> None:
        """
        Validates MASS Stage 1 & Stage 2 topological constraints:
          1. Exact cardinality of 21 agents (3 squads x 7 agents).
          2. Bijective agent_id and canonical_name mapping.
          3. Disjoint target_paths across all 21 agents (zero write collision).
          4. Acyclic causal dependency DAG converging on AG-21.
        """
        if len(self._agents) != self.EXPECTED_AGENT_COUNT:
            raise ValueError(f"Expected {self.EXPECTED_AGENT_COUNT} agents, found {len(self._agents)}")

        if len(self._by_id) != self.EXPECTED_AGENT_COUNT:
            raise ValueError("Duplicate ConsolidationAgentId detected in topology")

        names = {spec.canonical_name for spec in self._agents}
        if len(names) != self.EXPECTED_AGENT_COUNT:
            raise ValueError("Duplicate canonical_name detected in topology")

        for squad in ConsolidationSquad:
            count = sum(1 for spec in self._agents if spec.squad == squad)
            if count != self.SQUAD_SIZE:
                raise ValueError(f"Squad {squad.value} must have exactly {self.SQUAD_SIZE} agents, found {count}")

        # Verify disjoint target ownership (zero write collision)
        claimed_paths: Dict[str, ConsolidationAgentId] = {}
        for spec in self._agents:
            if not spec.target_paths:
                raise ValueError(f"Agent {spec.agent_id.value} has empty target_paths")
            for path in spec.target_paths:
                owner = claimed_paths.get(path)
                if owner is not None:
                    raise ValueError(
                        f"Write path collision on '{path}' between {owner.value} and {spec.agent_id.value}"
                    )
                claimed_paths[path] = spec.agent_id

        # Verify DAG acyclicity via topological wave resolution
        _ = self.compute_causal_waves()

    def compute_causal_waves(self) -> Tuple[Tuple[ConsolidationAgentSpec, ...], ...]:
        """
        Partitions the 21 agents into deterministic topological execution waves
        such that every agent in wave k depends only on agents in waves < k.
        """
        resolved: set[ConsolidationAgentId] = set()
        remaining: List[ConsolidationAgentSpec] = list(self._agents)
        waves: List[Tuple[ConsolidationAgentSpec, ...]] = []

        while remaining:
            ready = [spec for spec in remaining if all(dep in resolved for dep in spec.causal_dependencies)]
            if not ready:
                unresolved_ids = [spec.agent_id.value for spec in remaining]
                raise ValueError(f"Causal cycle detected among agents: {unresolved_ids}")

            waves.append(tuple(ready))
            for spec in ready:
                resolved.add(spec.agent_id)
            remaining = [spec for spec in remaining if spec.agent_id not in resolved]

        return tuple(waves)

    def project_markov_context(
        self,
        agent_id: ConsolidationAgentId,
        ledger_outcomes: Sequence[AgentGateOutcome],
    ) -> Tuple[AgentGateOutcome, ...]:
        """
        Markov Blanket Projection Operator P_mu (Delta I <= 0).
        Projects only direct causal dependency outcomes required by `agent_id`,
        capped by MAX_MARKOV_EVENTS for non-apex nodes.
        """
        spec = self._by_id[agent_id]
        dep_set = set(spec.causal_dependencies)
        projected = [out for out in ledger_outcomes if out.agent_id in dep_set]
        if agent_id != ConsolidationAgentId.AG_21:
            projected = projected[-self.MAX_MARKOV_EVENTS :]
        return tuple(projected)

    async def execute_consolidation(
        self,
        logical_tick: int,
        gate_evaluator: GateEvaluatorFn | None = None,
    ) -> ConsolidationSealReceipt:
        """
        Executes all 21 consolidation agents in topological waves and emits
        a deterministic ConsolidationSealReceipt anchored to `logical_tick`.
        """
        if logical_tick < 0:
            raise ValueError("logical_tick must be a non-negative integer")

        semaphore = asyncio.Semaphore(self.max_concurrency)
        outcomes_by_id: Dict[ConsolidationAgentId, AgentGateOutcome] = {}
        waves = self.compute_causal_waves()

        async def _eval_agent(spec: ConsolidationAgentSpec) -> AgentGateOutcome:
            async with semaphore:
                deps_ok = all(outcomes_by_id[dep].verified for dep in spec.causal_dependencies)
                if not deps_ok:
                    failed_deps = [dep.value for dep in spec.causal_dependencies if not outcomes_by_id[dep].verified]
                    detail = f"BLOCKED_BY_UPSTREAM:{','.join(failed_deps)}"
                    verified = False
                elif gate_evaluator is None:
                    verified = True
                    detail = f"GATE_SPEC_READY:{spec.gate_command}"
                else:
                    raw_res = gate_evaluator(spec, logical_tick)
                    if inspect.isawaitable(raw_res):
                        resolved_res = await raw_res
                    else:
                        resolved_res = raw_res

                    if isinstance(resolved_res, tuple):
                        verified, detail = bool(resolved_res[0]), str(resolved_res[1])
                    else:
                        verified = bool(resolved_res)
                        detail = "VERIFIED" if verified else "FAILED"

                ev_payload = (
                    f"EVIDENCE|{spec.agent_id.value}|{spec.invariant_id}|"
                    f"tick={logical_tick}|verified={verified}|{detail}"
                ).encode("utf-8")
                evidence_digest = _canonical_blake3_hex(ev_payload)
                return AgentGateOutcome(
                    agent_id=spec.agent_id,
                    canonical_name=spec.canonical_name,
                    verified=verified,
                    logical_tick=logical_tick,
                    evidence_digest=evidence_digest,
                    detail=detail,
                )

        for wave in waves:
            wave_results = await asyncio.gather(*(_eval_agent(spec) for spec in wave))
            for outcome in wave_results:
                outcomes_by_id[outcome.agent_id] = outcome

        ordered_outcomes = tuple(outcomes_by_id[spec.agent_id] for spec in self._agents)
        squad_digests: Dict[str, str] = {}
        for squad in ConsolidationSquad:
            squad_leaves = "|".join(outcomes_by_id[spec.agent_id].leaf_digest() for spec in self.squad_agents(squad))
            squad_raw = f"SQUAD_ROOT|{squad.value}|tick={logical_tick}|{squad_leaves}".encode("utf-8")
            squad_digests[squad.value] = _canonical_blake3_hex(squad_raw)

        merkle_payload = (
            f"BABYLON21_MERKLE_ROOT|v1|tick={logical_tick}|"
            + "|".join(f"{squad.value}:{squad_digests[squad.value]}" for squad in ConsolidationSquad)
        ).encode("utf-8")
        merkle_root_hex = _canonical_blake3_hex(merkle_payload)

        failed_agents = tuple(out.agent_id.value for out in ordered_outcomes if not out.verified)
        verified_count = sum(1 for out in ordered_outcomes if out.verified)

        return ConsolidationSealReceipt(
            logical_tick=logical_tick,
            total_agents=len(ordered_outcomes),
            verified_count=verified_count,
            failed_agents=failed_agents,
            squad_digests=squad_digests,
            merkle_root_hex=merkle_root_hex,
            consolidated=(verified_count == self.EXPECTED_AGENT_COUNT),
            outcomes=ordered_outcomes,
        )

    @staticmethod
    def create_subprocess_gate_evaluator(
        cwd: str | None = None,
        timeout_s: float = 60.0,
    ) -> GateEvaluatorFn:
        """
        Builds an asynchronous gate evaluator that executes each agent's
        canonical gate_command in a shell subprocess.
        """

        async def _evaluator(
            spec: ConsolidationAgentSpec,
            logical_tick: int,
        ) -> Tuple[bool, str]:
            try:
                proc = await asyncio.create_subprocess_shell(
                    spec.gate_command,
                    cwd=cwd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout_b, stderr_b = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout_s,
                )
                success = proc.returncode == 0
                out_tail = (stdout_b + stderr_b)[-200:].decode("utf-8", errors="replace").strip()
                detail = f"EXIT_{proc.returncode}:{out_tail}" if not success else "VERIFIED_SILICON_GATE"
                return success, detail
            except asyncio.TimeoutError:
                return False, f"TIMEOUT_AFTER_{timeout_s}s"
            except Exception as e:
                return False, f"EXEC_ERROR:{str(e)}"

        return _evaluator
