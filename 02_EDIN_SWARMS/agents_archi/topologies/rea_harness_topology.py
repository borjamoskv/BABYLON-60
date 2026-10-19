#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ REA HARNESS SWARM TOPOLOGY | DOMAIN: agents_archi.topologies | STATE: C5-REAL
# ============================================================================
"""
Topología de Agente Maestro REA con Subagentes REA (`ReaHarnessSwarmTopology`).
===============================================================================
Orquesta en sala limpia (`RFO=0`, cero demonios Node.js ni `npx rea-agents`) la
disección AOT y síntesis de puentes soberanos sobre tres ecosistemas de arneses:
  1. `ReaSubagentClawCode` (`claw-code`): Binarios Rust Mach-O 64 + bucle CLI.
  2. `ReaSubagentOpenClaw` (`openclaw`): Pasarela TypeScript, `soul.md` + `tether.md` + `INV-Ω`.
  3. `ReaSubagentDeepSeekHarness` (`deepseek-harness`): Electron `.asar` + Cordis Plugins + P x S Cap.

Cumple:
  - Invariante de Topología Causal (MASS Stage 1 Block-Level + Stage 2 Kahn DAG).
  - Cortafuegos 16 (Clean-Room AOT Dissection) y Cortafuegos 17 (<= 150 tokens).
  - Memoria Acotada KDA O(1) (`AX-KDA-1` <= 8.192 B/slot) y `ThermalLock`.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Awaitable, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from agents_archi.orchestrator.kda_dag_swarm import (
    KdaSwarmMemory,
    KahnDagSwarmScheduler,
    SwarmDagNode,
)
from babylon60.transducers.clean_room_aot_dissector import (
    CleanRoomAotDissector,
    HarnessSubagentDissectionReport,
    HarnessTargetKind,
    MAX_AOT_GRAMMAR_TOKENS,
    SovereignHarnessAotBridge,
)


@dataclass(frozen=True)
class ReaSwarmConsolidationReceipt:
    """Recibo inmutable consolidado por el Agente Maestro REA tras ejecutar sus Subagentes."""

    logical_tick: int
    targets_evaluated: Tuple[str, ...]
    dag_execution_order: Tuple[str, ...]
    total_original_states: int
    total_minimal_states: int
    aggregate_pruning_ratio: float
    max_grammar_tokens_observed: int
    cortafuegos_17_passed: bool
    all_subagents_verified: bool
    subagent_reports: Tuple[HarnessSubagentDissectionReport, ...]
    aot_bridges: Tuple[SovereignHarnessAotBridge, ...]
    merkle_root_sha256: str


class _BaseReaHarnessSubagent:
    """Primitiva Nivel Bloque (MASS Stage 1) para un Subagente REA especialista."""

    def __init__(self, target_kind: HarnessTargetKind, subagent_id: str) -> None:
        self.target_kind = target_kind
        self.subagent_id = subagent_id

    def execute_isolated(
        self,
        overrides: Optional[Mapping[str, Any]] = None,
    ) -> HarnessSubagentDissectionReport:
        """
        Ejecuta la disección AOT en memoria de forma independiente (Stage 1 Block-Level).
        Puede invocarse sin necesidad de instanciar el planificador DAG.
        """
        kwargs: Dict[str, Any] = dict(overrides) if overrides else {}
        return CleanRoomAotDissector.dissect_external_harness_target(
            self.target_kind,
            **kwargs,
        )

    async def run_kda_node(
        self,
        memory: KdaSwarmMemory,
        overrides: Optional[Mapping[str, Any]] = None,
    ) -> HarnessSubagentDissectionReport:
        """
        Ejecuta el subagente dentro del DAG de Kahn y deposita el resumen compacto
        en `KdaSwarmMemory` respetando estrictamente `MAX_SLOT_BYTES` (8.192 B).
        """
        report = self.execute_isolated(overrides=overrides)
        compact_slot = {
            "target_kind": report.target_kind,
            "subagent_id": report.subagent_id,
            "binary_format": report.binary_format,
            "header_valid": report.header_valid,
            "original_states": report.quotient.original_state_count,
            "minimal_states": report.quotient.minimal_state_count,
            "pruning_ratio": report.quotient.anergy_pruning_ratio,
            "requested_concurrency": report.requested_concurrency,
            "recommended_concurrency_cap": report.recommended_concurrency_cap,
            "grammar_tokens": report.grammar_tokens,
            "verdict_code": report.verdict_code,
            "scitt_subagent_hash": report.scitt_subagent_hash,
        }
        payload = json.dumps(compact_slot, sort_keys=True, separators=(",", ":")).encode("utf-8")
        await memory.put(f"stage:rea:sub:{self.target_kind.value}", payload)
        return report


class ReaSubagentClawCode(_BaseReaHarnessSubagent):
    """
    Subagente REA especializado en `claw-code` (Rust Mach-O 64 ARM64 + bucle CLI).
    Purga residuos de source-maps (`cli.js.map`, `spinner_verbs`, `undercover_mode`) y
    verifica alineación `align(64)` y barreras Seqlock en Anillo-0.
    """

    def __init__(self) -> None:
        super().__init__(HarnessTargetKind.CLAW_CODE, "rea-subagent:claw-code")


class ReaSubagentOpenClaw(_BaseReaHarnessSubagent):
    """
    Subagente REA especializado en `OpenClaw` (TypeScript Gateway + `soul.md` + Skills).
    Audita la mediación completa `INV-Ω` (`BabylonBroker`), el anclaje criptográfico de
    `soul.md`/`tether.md` y el confinamiento visual fail-closed.
    """

    def __init__(self) -> None:
        super().__init__(HarnessTargetKind.OPENCLAW, "rea-subagent:openclaw")


class ReaSubagentDeepSeekHarness(_BaseReaHarnessSubagent):
    """
    Subagente REA especializado en `DeepSeek Harness` (`dsh` v0.2 Electron `.asar` + Cordis).
    Bloquea plugins de sesión emulada (`dsh-chatgpt-sub`), poda el grafo de estados Cordis
    y limita la concurrencia de *Agent Teams* al techo físico Apple Silicon P x S (12).
    """

    def __init__(self) -> None:
        super().__init__(HarnessTargetKind.DEEPSEEK_HARNESS, "rea-subagent:deepseek-harness")


class ReaHarnessSwarmTopology:
    """
    Topología de Enjambre REA (Nivel Workflow — MASS Stage 2):
      - `node:rea_master_intake`: Agente Maestro REA (partición e ingesta en KDA).
      - `node:rea_sub_claw_code`: Subagente REA para `claw-code`.
      - `node:rea_sub_openclaw`: Subagente REA para `OpenClaw`.
      - `node:rea_sub_dsh`: Subagente REA para `DeepSeek Harness`.
      - `node:rea_quotient_reducer`: Reductor conjunto Myhill-Nerode y Gate Cortafuegos 17.
      - `node:rea_scitt_bridge_seal`: Sintetizador de puentes AOT y árbol de Merkle SCITT.
    """

    SUBAGENT_NODE_MAP: Mapping[str, str] = {
        HarnessTargetKind.CLAW_CODE.value: "node:rea_sub_claw_code",
        HarnessTargetKind.OPENCLAW.value: "node:rea_sub_openclaw",
        HarnessTargetKind.DEEPSEEK_HARNESS.value: "node:rea_sub_dsh",
    }

    def __init__(
        self,
        concurrency_limit: int = 6,
        memory_capacity: int = 128,
        loopback_port: int = 6061,
    ) -> None:
        self.concurrency_limit = concurrency_limit
        self.memory = KdaSwarmMemory(capacity=memory_capacity)
        self.scheduler = KahnDagSwarmScheduler(concurrency_limit=concurrency_limit)
        self.loopback_port = loopback_port
        self.subagents: Dict[str, _BaseReaHarnessSubagent] = {
            HarnessTargetKind.CLAW_CODE.value: ReaSubagentClawCode(),
            HarnessTargetKind.OPENCLAW.value: ReaSubagentOpenClaw(),
            HarnessTargetKind.DEEPSEEK_HARNESS.value: ReaSubagentDeepSeekHarness(),
        }

    @staticmethod
    def _compute_merkle_root(leaves: Sequence[str]) -> str:
        if not leaves:
            return hashlib.sha256(b"BABYLON60/REA-SWARM-EMPTY/v1").hexdigest()
        layer = [hashlib.sha256(leaf.encode("utf-8")).hexdigest() for leaf in leaves]
        while len(layer) > 1:
            next_layer: List[str] = []
            for idx in range(0, len(layer), 2):
                left = layer[idx]
                right = layer[idx + 1] if idx + 1 < len(layer) else left
                combined = hashlib.sha256(f"{left}:{right}".encode("utf-8")).hexdigest()
                next_layer.append(combined)
            layer = next_layer
        return layer[0]

    async def execute_rea_swarm(
        self,
        targets: Optional[Sequence[str | HarnessTargetKind]] = None,
        *,
        logical_tick: int = 60,
        target_overrides: Optional[Mapping[str, Mapping[str, Any]]] = None,
        lock_path: Optional[str] = None,
    ) -> ReaSwarmConsolidationReceipt:
        """
        Ejecuta el DAG acíclico completo del Agente Maestro REA y sus Subagentes REA.
        """
        if targets is None:
            selected_targets = [
                HarnessTargetKind.CLAW_CODE.value,
                HarnessTargetKind.OPENCLAW.value,
                HarnessTargetKind.DEEPSEEK_HARNESS.value,
            ]
        else:
            selected_targets = []
            for t in targets:
                val = t.value if isinstance(t, HarnessTargetKind) else str(t).strip().lower()
                if val not in self.subagents:
                    raise ValueError(f"Unsupported REA harness target: {t}")
                if val not in selected_targets:
                    selected_targets.append(val)

        if not selected_targets:
            raise ValueError("At least one REA harness target must be specified.")

        overrides_map: Mapping[str, Mapping[str, Any]] = target_overrides or {}
        collected_reports: Dict[str, HarnessSubagentDissectionReport] = {}
        collected_bridges: Dict[str, SovereignHarnessAotBridge] = {}

        # ── N0: AGENTE MAESTRO REA (INGESTA Y PARTICIÓN) ────────────────────
        async def _master_intake_task(mem: KdaSwarmMemory) -> Dict[str, Any]:
            intake_doc = {
                "logical_tick": logical_tick,
                "targets": selected_targets,
                "max_aot_grammar_tokens": MAX_AOT_GRAMMAR_TOKENS,
            }
            await mem.put(
                "stage:rea:intake",
                json.dumps(intake_doc, sort_keys=True, separators=(",", ":")).encode("utf-8"),
            )
            return intake_doc

        # ── N1: ESCUADRÓN DE SUBAGENTES REA EN PARALELO ─────────────────────
        def _make_subagent_task(
            target_key: str,
        ) -> Callable[[KdaSwarmMemory], Awaitable[HarnessSubagentDissectionReport]]:
            subagent = self.subagents[target_key]
            custom_ovr = overrides_map.get(target_key)

            async def _task(mem: KdaSwarmMemory) -> HarnessSubagentDissectionReport:
                rep = await subagent.run_kda_node(mem, overrides=custom_ovr)
                collected_reports[target_key] = rep
                return rep

            return _task

        # ── N2: REDUCTOR CONJUNTO MYHILL-NERODE Y CORTAFUEGOS 17 ────────────
        async def _quotient_reducer_task(mem: KdaSwarmMemory) -> Dict[str, Any]:
            orig_total = 0
            min_total = 0
            max_tok = 0
            all_budget_ok = True
            for t_key in selected_targets:
                rep = collected_reports[t_key]
                orig_total += rep.quotient.original_state_count
                min_total += rep.quotient.minimal_state_count
                max_tok = max(max_tok, rep.grammar_tokens)
                if rep.grammar_tokens > MAX_AOT_GRAMMAR_TOKENS:
                    all_budget_ok = False

            agg_pruning = round(1.0 - (min_total / orig_total), 6) if orig_total > 0 else 0.0
            summary = {
                "total_original_states": orig_total,
                "total_minimal_states": min_total,
                "aggregate_pruning_ratio": agg_pruning,
                "max_grammar_tokens_observed": max_tok,
                "cortafuegos_17_passed": all_budget_ok,
            }
            await mem.put(
                "stage:rea:quotient",
                json.dumps(summary, sort_keys=True, separators=(",", ":")).encode("utf-8"),
            )
            return summary

        # ── N3: SÍNTESIS DE PUENTES AOT Y SELLADO MERKLE SCITT ──────────────
        async def _scitt_bridge_seal_task(mem: KdaSwarmMemory) -> str:
            leaves: List[str] = []
            for t_key in selected_targets:
                rep = collected_reports[t_key]
                bridge = CleanRoomAotDissector.synthesize_harness_aot_bridge(
                    rep,
                    loopback_port=self.loopback_port,
                )
                collected_bridges[t_key] = bridge
                leaves.append(f"{t_key}:{rep.scitt_subagent_hash}:{bridge.bridge_digest_sha256}")

            merkle_root = self._compute_merkle_root(leaves)
            await mem.put("stage:rea:seal", merkle_root.encode("utf-8"))
            return merkle_root

        # Construir el DAG acíclico en KahnDagSwarmScheduler
        self.scheduler.nodes.clear()
        self.scheduler.add_node(SwarmDagNode("node:rea_master_intake", [], _master_intake_task))

        active_sub_nodes: List[str] = []
        for t_key in selected_targets:
            node_name = self.SUBAGENT_NODE_MAP[t_key]
            active_sub_nodes.append(node_name)
            self.scheduler.add_node(SwarmDagNode(node_name, ["node:rea_master_intake"], _make_subagent_task(t_key)))

        self.scheduler.add_node(SwarmDagNode("node:rea_quotient_reducer", active_sub_nodes, _quotient_reducer_task))
        self.scheduler.add_node(
            SwarmDagNode("node:rea_scitt_bridge_seal", ["node:rea_quotient_reducer"], _scitt_bridge_seal_task)
        )

        dag_order = await self.scheduler.execute_dag(self.memory, lock_path=lock_path)

        raw_quotient = await self.memory.get("stage:rea:quotient")
        quotient_meta = json.loads(raw_quotient.decode("utf-8")) if raw_quotient else {}
        raw_seal = await self.memory.get("stage:rea:seal")
        merkle_root_hex = raw_seal.decode("utf-8") if raw_seal else ""

        ordered_reports = tuple(collected_reports[t_key] for t_key in selected_targets)
        ordered_bridges = tuple(collected_bridges[t_key] for t_key in selected_targets)
        all_verified = all(r.verdict_code == "REA_SUBAGENT_AOT_VERIFIED" for r in ordered_reports)

        return ReaSwarmConsolidationReceipt(
            logical_tick=logical_tick,
            targets_evaluated=tuple(selected_targets),
            dag_execution_order=tuple(dag_order),
            total_original_states=int(quotient_meta.get("total_original_states", 0)),
            total_minimal_states=int(quotient_meta.get("total_minimal_states", 0)),
            aggregate_pruning_ratio=float(quotient_meta.get("aggregate_pruning_ratio", 0.0)),
            max_grammar_tokens_observed=int(quotient_meta.get("max_grammar_tokens_observed", 0)),
            cortafuegos_17_passed=bool(quotient_meta.get("cortafuegos_17_passed", False)),
            all_subagents_verified=all_verified,
            subagent_reports=ordered_reports,
            aot_bridges=ordered_bridges,
            merkle_root_sha256=merkle_root_hex,
        )

    @staticmethod
    def receipt_to_dict(receipt: ReaSwarmConsolidationReceipt) -> Dict[str, Any]:
        """Serializa el recibo consolidado a un diccionario JSON determinista."""
        return asdict(receipt)
