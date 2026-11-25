#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ BABYLON-21 CONSOLIDATION TESTS | DOMAIN: 02_EDIN_SWARMS | STATE: C5-REAL
# ============================================================================
"""
Empirical verification suite for the 21-Agent BABYLON-60 Consolidation Topology.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
import sys
import pytest

SWARMS_ROOT = Path(__file__).resolve().parents[1]
if str(SWARMS_ROOT) not in sys.path:
    sys.path.insert(0, str(SWARMS_ROOT))

from agents_archi.topologies import (  # noqa: E402
    BABYLON21_AGENTS,
    Babylon21ConsolidationTopology,
    ConsolidationAgentId,
    ConsolidationAgentSpec,
    ConsolidationSquad,
    SwarmRouter,
    TopologyTarget,
)


def test_babylon21_exact_cardinality_and_triadic_squads() -> None:
    """Verifies 21 agents partitioned into 3 squads of 7 with disjoint write targets."""
    topology = Babylon21ConsolidationTopology()
    assert len(topology.agents) == 21

    for squad in ConsolidationSquad:
        squad_members = topology.squad_agents(squad)
        assert len(squad_members) == 7

    waves = topology.compute_causal_waves()
    assert len(waves) >= 3
    # Final wave must be the single Apex BFT Seal agent (AG-21)
    assert len(waves[-1]) == 1
    assert waves[-1][0].agent_id == ConsolidationAgentId.AG_21


def test_babylon21_rejects_write_path_collision() -> None:
    """Falsifies MASS Stage 1 when two agents share a mutable target path."""
    mutated = list(BABYLON21_AGENTS)
    ag01 = mutated[0]
    mutated[1] = replace(mutated[1], target_paths=(ag01.target_paths[0],))

    with pytest.raises(ValueError, match="Write path collision"):
        Babylon21ConsolidationTopology(agents=mutated)


def test_babylon21_rejects_causal_cycle() -> None:
    """Falsifies DAG acyclicity when a circular dependency is injected."""
    mutated = list(BABYLON21_AGENTS)
    mutated[0] = replace(
        mutated[0],
        causal_dependencies=(ConsolidationAgentId.AG_08,),
    )

    with pytest.raises(ValueError, match="Causal cycle detected"):
        Babylon21ConsolidationTopology(agents=mutated)


def test_babylon21_deterministic_logical_tick_merkle_seal() -> None:
    """Verifies INV_C5_CANONICAL_LOGICAL_TICK determinism across executions."""
    topology = Babylon21ConsolidationTopology()

    receipt_a = asyncio.run(topology.execute_consolidation(logical_tick=60))
    receipt_b = asyncio.run(topology.execute_consolidation(logical_tick=60))
    receipt_c = asyncio.run(topology.execute_consolidation(logical_tick=61))

    assert receipt_a.consolidated is True
    assert receipt_a.total_agents == 21
    assert receipt_a.verified_count == 21
    assert receipt_a.failed_agents == ()
    assert receipt_a.merkle_root_hex == receipt_b.merkle_root_hex
    assert receipt_a.merkle_root_hex != receipt_c.merkle_root_hex


def test_babylon21_upstream_failure_blocks_dependents_and_apex() -> None:
    """Verifies fail-closed propagation when AG-04 (LARSA BFT WAL) fails."""
    topology = Babylon21ConsolidationTopology()

    def _fault_injector(spec: ConsolidationAgentSpec, tick: int) -> tuple[bool, str]:
        if spec.agent_id == ConsolidationAgentId.AG_04:
            return False, f"FAULT_INJECTED_AT_TICK_{tick}"
        return True, "OK"

    receipt = asyncio.run(
        topology.execute_consolidation(logical_tick=120, gate_evaluator=_fault_injector)
    )
    assert receipt.consolidated is False
    assert "AG-04" in receipt.failed_agents
    assert "AG-07" in receipt.failed_agents
    assert "AG-09" in receipt.failed_agents
    assert "AG-13" in receipt.failed_agents
    assert "AG-21" in receipt.failed_agents


def test_babylon21_markov_blanket_projection_bounds() -> None:
    """Verifies Markov Blanket projection filters only direct dependencies."""
    topology = Babylon21ConsolidationTopology()
    receipt = asyncio.run(topology.execute_consolidation(logical_tick=42))

    # AG-08 depends only on AG-01
    projected_ag08 = topology.project_markov_context(
        ConsolidationAgentId.AG_08, receipt.outcomes
    )
    assert len(projected_ag08) == 1
    assert projected_ag08[0].agent_id == ConsolidationAgentId.AG_01

    # AG-21 (Apex) receives all 20 upstream agent outcomes
    projected_ag21 = topology.project_markov_context(
        ConsolidationAgentId.AG_21, receipt.outcomes
    )
    assert len(projected_ag21) == 20


def test_swarm_router_dispatches_babylon21_queries() -> None:
    """Verifies SwarmRouter maps natural language 21-agent queries to BABYLON_21_CONSOLIDATION."""
    target, confidence = SwarmRouter.route_query(
        "Crea 21 agentes para consolidar BABYLON 60"
    )
    assert target == TopologyTarget.BABYLON_21_CONSOLIDATION
    assert confidence == 1.0

    fuzzy_target, fuzzy_conf = SwarmRouter.route_query("babylon21")
    assert fuzzy_target == TopologyTarget.BABYLON_21_CONSOLIDATION
    assert fuzzy_conf >= 0.8


def test_babylon21_subprocess_evaluator() -> None:
    """Verifies create_subprocess_gate_evaluator accurately catches exit codes and outputs."""
    topology = Babylon21ConsolidationTopology()
    evaluator = topology.create_subprocess_gate_evaluator(timeout_s=5.0)

    async def _exercise() -> None:
        mock_spec = replace(
            topology.get_agent(ConsolidationAgentId.AG_01),
            gate_command="true",
        )
        res_ok = evaluator(mock_spec, 100)
        assert not isinstance(res_ok, (bool, tuple))
        outcome_ok = await res_ok
        assert isinstance(outcome_ok, tuple)
        success, detail = outcome_ok
        assert success is True
        assert detail == "VERIFIED_SILICON_GATE"

        mock_failing_spec = replace(
            topology.get_agent(ConsolidationAgentId.AG_01),
            gate_command="exit 7",
        )
        res_fail = evaluator(mock_failing_spec, 100)
        assert not isinstance(res_fail, (bool, tuple))
        outcome_fail = await res_fail
        assert isinstance(outcome_fail, tuple)
        fail_res, fail_detail = outcome_fail
        assert fail_res is False
        assert "EXIT_7" in fail_detail

    asyncio.run(_exercise())


def test_babylon21_cli_subcommand_json() -> None:
    """Verifies babylon60 consolidate-21 --json emits deterministic ConsolidationSealReceipt JSON."""
    import json
    import subprocess

    repo_root = SWARMS_ROOT.parent
    dispatcher = repo_root / "01_KISH_ENGINE" / "babylon60" / "cli" / "main_dispatcher.py"
    res = subprocess.run(
        [sys.executable, str(dispatcher), "consolidate-21", "--tick", "60", "--json"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(res.stdout)
    assert payload["logical_tick"] == 60
    assert payload["total_agents"] == 21
    assert payload["verified_count"] == 21
    assert payload["consolidated"] is True
    assert len(payload["outcomes"]) == 21

