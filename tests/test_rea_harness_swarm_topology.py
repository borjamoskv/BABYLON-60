#!/usr/bin/env python3
"""
test_rea_harness_swarm_topology.py — Suite de Verificación del Enjambre REA y Subagentes
========================================================================================
Valida deterministamente en silicio (`RFO=0`):
  1. Validación Nivel Bloque (MASS Stage 1): Independencia causal de `ReaSubagentClawCode`,
     `ReaSubagentOpenClaw` y `ReaSubagentDeepSeekHarness`.
  2. Validación Nivel Workflow (MASS Stage 2): Ejecución del DAG acíclico en `KahnDagSwarmScheduler`
     acoplado a `KdaSwarmMemory` (<= 8.192 B/slot) y sellado de raíz de Merkle SCITT.
  3. Cumplimiento de `INV_C5_OPSEC_CALIBRATION` (cero rutas `/Users/` en manifiestos AOT)
     y Cortafuegos 17 (<= 150 tokens por gramática de despacho).
  4. Despacho CLI extremo a extremo (`babylon60 rea {status,dissect,swarm,bridge} --json`).
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for sub in ("01_KISH_ENGINE", "02_EDIN_SWARMS"):
    p = os.path.join(REPO_ROOT, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

from agents_archi.topologies import (  # noqa: E402
    ReaHarnessSwarmTopology,
    ReaSubagentClawCode,
    ReaSubagentDeepSeekHarness,
    ReaSubagentOpenClaw,
)
from babylon60.transducers.clean_room_aot_dissector import (  # noqa: E402
    APPLE_SILICON_PXS_SUBAGENT_CAP,
    HarnessTargetKind,
    MAX_AOT_GRAMMAR_TOKENS,
)


def test_mass_stage1_isolated_rea_subagents() -> None:
    """Verifica que cada Subagente REA opera de forma independiente antes de componerse en el DAG."""
    sub_claw = ReaSubagentClawCode()
    rep_claw = sub_claw.execute_isolated()
    assert rep_claw.subagent_id == "rea-subagent:claw-code"
    assert rep_claw.verdict_code == "REA_SUBAGENT_AOT_VERIFIED"
    assert rep_claw.quotient.minimal_state_count == 3

    sub_open = ReaSubagentOpenClaw()
    rep_open = sub_open.execute_isolated()
    assert rep_open.subagent_id == "rea-subagent:openclaw"
    assert rep_open.verdict_code == "REA_SUBAGENT_AOT_VERIFIED"
    assert "unmediated_fs_write" in rep_open.unmediated_authority_risks

    sub_dsh = ReaSubagentDeepSeekHarness()
    rep_dsh = sub_dsh.execute_isolated()
    assert rep_dsh.subagent_id == "rea-subagent:deepseek-harness"
    assert rep_dsh.verdict_code == "REA_SUBAGENT_AOT_VERIFIED"
    assert rep_dsh.requested_concurrency == 50
    assert rep_dsh.recommended_concurrency_cap == APPLE_SILICON_PXS_SUBAGENT_CAP


def test_mass_stage2_rea_harness_kahn_dag_and_kda_memory() -> None:
    """Verifica la topología completa `ReaHarnessSwarmTopology` sobre Kahn DAG y memoria KDA."""
    topology = ReaHarnessSwarmTopology(concurrency_limit=4, memory_capacity=64)
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_file = os.path.join(tmpdir, ".test_rea_swarm.lock")
        receipt = asyncio.run(
            topology.execute_rea_swarm(
                targets=[
                    HarnessTargetKind.CLAW_CODE,
                    HarnessTargetKind.OPENCLAW,
                    HarnessTargetKind.DEEPSEEK_HARNESS,
                ],
                logical_tick=120,
                lock_path=lock_file,
            )
        )

    assert receipt.logical_tick == 120
    assert receipt.targets_evaluated == ("claw-code", "openclaw", "deepseek-harness")
    assert receipt.dag_execution_order[0] == "node:rea_master_intake"
    assert receipt.dag_execution_order[-2] == "node:rea_quotient_reducer"
    assert receipt.dag_execution_order[-1] == "node:rea_scitt_bridge_seal"
    assert receipt.total_original_states == 20
    assert receipt.total_minimal_states == 9
    assert receipt.aggregate_pruning_ratio == 0.55
    assert receipt.cortafuegos_17_passed is True
    assert receipt.max_grammar_tokens_observed <= MAX_AOT_GRAMMAR_TOKENS
    assert receipt.all_subagents_verified is True
    assert len(receipt.merkle_root_sha256) == 64

    # Verificar que los slots KDA fueron escritos y que ningún manifiesto contiene `/Users/`
    serialized = json.dumps(topology.receipt_to_dict(receipt))
    assert "/Users/" not in serialized


def test_cli_babylon60_rea_subcommands_end_to_end() -> None:
    """Verifica el despacho CLI de `babylon60 rea` para `status`, `dissect`, `bridge` y `swarm`."""
    dispatcher = os.path.join(REPO_ROOT, "01_KISH_ENGINE", "babylon60", "cli", "main_dispatcher.py")

    for subcmd in ("status", "dissect", "bridge", "swarm"):
        proc = subprocess.run(
            [sys.executable, dispatcher, "rea", subcmd, "--target", "all", "--json"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, f"CLI rea {subcmd} failed: {proc.stderr}"
        payload = json.loads(proc.stdout)
        assert isinstance(payload, dict)
        assert "/Users/" not in proc.stdout
