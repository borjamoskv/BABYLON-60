#!/usr/bin/env python3
"""Run a synthetic Destiladora demonstration in a disposable child process.

The demonstration never records observations in the operational ledger or
writes repository sources. It stops before Rust generation while proof and
implementation correspondence remain unverified. It is not a benchmark or
hardware attestation.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).absolute().parents[2]
_CREDENTIAL_KEYS = (
    "CORTEX_VAULT_KEY", "KIMI_API_KEY", "MOONSHOT_API_KEY", "OPENROUTER_API_KEY",
    "OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "BABYLON60_SIGNING_SEED",
)


def _set_demo_paths(root: Path, environment: MutableMapping[str, str]) -> None:
    for key, value in {
        "HOME": root / "home",
        "XDG_CONFIG_HOME": root / "config",
        "XDG_DATA_HOME": root / "data",
        "XDG_CACHE_HOME": root / "cache",
        "BABYLON_HOME": root,
        "CORTEX_HOME": root / "cortex",
        "CORTEX_MEMORY_DB": root / "cortex_memory.db",
    }.items():
        environment[key] = str(value)
    for key in _CREDENTIAL_KEYS:
        environment.pop(key, None)


def _run_isolated_demo() -> dict[str, Any]:
    # The worker allocates its own root. A caller cannot supply an operator path.
    with tempfile.TemporaryDirectory(prefix="b60-destiladora-worker-") as directory:
        root = Path(directory)
        _set_demo_paths(root, os.environ)
        Path(os.environ["HOME"]).mkdir()
        os.chdir(root)
        # Configure isolation before importing any pipeline component.
        sys.path.insert(0, str(BASE_DIR / "scripts/c5_destiladora"))
        from goal_trace_ingestor import ingest_goal_trace
        from invariant_extractor_z3 import Z3InvariantExtractor
        from proof_emitter_lean4 import Lean4ProofEmitter

        db_path = root / "cortex_memory.db"
        trace_ids = []
        for index in range(3):
            trace_ids.append(ingest_goal_trace(
                conversation_id=f"synthetic-demo-{index}",
                contract_text="SYNTHETIC: parity demonstration, no observed execution",
                model_assigned="SYNTHETIC_FIXTURE",
                thinking_level="NOT_APPLICABLE",
                files_touched=["fixture/a.rs", "fixture/b.rs"],
                tool_sequence=[{"tool": "synthetic_fixture", "args": {}}],
                output_diff="SYNTHETIC_ONLY",
                exit_gate_cmd="SYNTHETIC_NOT_EXECUTED",
                exit_gate_code=0,
                usage_metadata={},
                latency_ms=0.0,
                db_path=db_path,
            ))
        extracted = Z3InvariantExtractor(db_path=db_path).inspect_and_extract(min_samples=2)
        proofs = Lean4ProofEmitter(db_path=db_path, lean_dir=root / "lean").prove_extracted_clusters()
        report = {
            "status": "NOT_VERIFIED",
            "synthetic": True,
            "temporary_root": str(root),
            "database": str(db_path),
            "home": os.environ["HOME"],
            "trace_count": len(trace_ids),
            "extraction": extracted,
            "proofs": proofs,
            "rust_generation": "NOT_EXECUTED",
            "native_compilation": "NOT_EXECUTED",
            "hardware_attestation": "NOT_EXECUTED",
            "benchmark": "NOT_EXECUTED",
            "reason": "IMPLEMENTATION_CORRESPONDENCE_UNVERIFIED",
        }
    report["temporary_files_removed"] = True
    return report


def run_end_to_end_test() -> bool:
    """Return failure until a complete, supported verified pipeline exists."""
    with tempfile.TemporaryDirectory(prefix="b60-destiladora-launcher-") as directory:
        environment = dict(os.environ)
        _set_demo_paths(Path(directory), environment)
        try:
            process = subprocess.run(
                [sys.executable, str(Path(__file__).absolute()), "--isolated-demo"],
                cwd=directory,
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired):
            print("Destiladora demonstration did not complete", file=sys.stderr)
            return False
        print(process.stdout, end="")
        if process.stderr:
            print(process.stderr, file=sys.stderr, end="")
        return process.returncode == 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--isolated-demo"]:
        print(json.dumps(_run_isolated_demo(), indent=2))
        sys.exit(2)
    if sys.argv[1:]:
        raise SystemExit("No database or output path arguments are accepted")
    sys.exit(0 if run_end_to_end_test() else 1)
