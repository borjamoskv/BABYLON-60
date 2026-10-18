# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | ENTROPY SYNTHESIS & APEX TEST SUITE | STATE: C5-REAL
# ============================================================================
from __future__ import annotations

import asyncio
import mmap
import shutil
import subprocess
from pathlib import Path

from agents_archi.orchestrator.seqlock_swarm_ring0 import (
    MANIFEST_SIZE,
    SeqlockSwarmChannel,
)
from babylon60.core.thermal_lock import POISONED_STATE, RUNNING_STATE
from babylon60.transducers.fisher_bayesian_gate import (
    FisherBayesianEntropyGate,
    FisherInformationGeometry,
)
from scripts.c5_quality_gates.audit_entropy_3strata import (
    audit_stratum_1,
    audit_stratum_3,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_i1_seqlock_mmap_affine_close() -> None:
    """[I1] Ensures SeqlockSwarmChannel.close() releases C-ABI buffer pointers before mmap.close()."""
    mm = mmap.mmap(-1, MANIFEST_SIZE)
    with SeqlockSwarmChannel.from_mmap(mm, 0) as channel:
        seq = channel.write(60, 1, b"AFFINE_TEST_HASH", flags=1)
        read_res = channel.read()
        assert read_res is not None
        assert read_res[0] == seq
        assert not channel.is_locked()
    assert mm.closed


def test_i2_stratum_1_and_3_gates() -> None:
    """[I2] Verifies Darwin TRNG entropy (>99.95%) and KISH Stratum 3 gate."""
    s1 = audit_stratum_1(sample_size=65536)
    assert s1["passed"] is True
    assert s1["shannon_entropy"] >= 7.9960
    assert s1["haveged_active"] is False
    assert s1["rng_tools_active"] is False

    s3 = audit_stratum_3(REPO_ROOT)
    assert s3["passed"] is True
    assert s3["min_exergy_pct"] >= 90.0
    assert s3["max_slop_density"] == 0.0


def test_i3_fisher_pythagorean_and_inline_gate() -> None:
    """[I3] Verifies Fisher-Rao Pythagorean identity and MUSHUSHU-0 poisoning on LLM slop."""
    r = [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]
    q_proj = [0.5, 0.25, 0.25]
    p = [0.5, 0.4, 0.1]
    valid, residual = FisherInformationGeometry.verify_pythagorean_identity(p, q_proj, r)
    assert valid is True
    assert residual < 1e-12

    async def _run_gate() -> None:
        gate = FisherBayesianEntropyGate()
        clean_text = (
            "El contrato KUDURRU-64 opera en una línea de caché L1 de 64 bytes "
            "mediante un protocolo Seqlock SPMC sin lecturas desgarradas."
        )
        v_clean = await gate.evaluate_transition(clean_text)
        assert v_clean.allowed is True
        assert v_clean.state_flag == RUNNING_STATE

        slop_text = (
            "¡Claro, aquí tienes el código! Espero que esto ayude. Como modelo de lenguaje, "
            "no dudes en preguntar si necesitas algo más. I hope this helps!"
        )
        v_slop = await gate.evaluate_transition(slop_text)
        assert v_slop.allowed is False
        assert v_slop.state_flag == POISONED_STATE
        assert gate.thermal_lock.is_poisoned is True

        # Subsequent clean write must also be blocked while poisoned
        v_after = await gate.evaluate_transition(clean_text)
        assert v_after.allowed is False
        assert v_after.state_flag == POISONED_STATE

    asyncio.run(_run_gate())


def test_i4_lean4_standalone_oracle() -> None:
    """[I4] Verifies standalone Lean 4 Core compilation of entropy_synthesis_omega.lean."""
    lean_bin = shutil.which("lean") or "/opt/homebrew/bin/lean"
    lean_file = REPO_ROOT / "crates/b60-lang/examples/entropy_synthesis_omega.lean"
    assert lean_file.is_file()
    if Path(lean_bin).is_file():
        res = subprocess.run([lean_bin, str(lean_file)], capture_output=True, text=True, check=False)
        assert res.returncode == 0, f"Lean 4 verification failed: {res.stdout}\n{res.stderr}"
