#!/usr/bin/env python3
"""Observe the real sandbox denial using only a disposable outside-write witness."""

import asyncio
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


root = Path(__file__).absolute().parents[4]
sys.path.insert(0, str(root / "01_KISH_ENGINE"))

from babylon60.kernel.mcp_deductive_engine import McpCandidateContract  # noqa: E402
from babylon60.kernel.mcp_sandbox_validator import McpSandboxValidator  # noqa: E402


with tempfile.TemporaryDirectory(prefix="b60-os-gate-witness-") as directory:
    fixture = Path(directory)
    witness = fixture / "outside-write"
    candidate = fixture / "candidate.py"
    candidate.write_text(
        "from pathlib import Path\nimport sys\ntry:\n"
        f"    Path({str(witness)!r}).write_text('unauthorized fixture write')\n"
        "except OSError as error:\n"
        "    print(f'DENIAL errno={error.errno} type={type(error).__name__}', file=sys.stderr)\n"
        "    raise SystemExit(73)\n"
        "raise SystemExit(74)\n"
    )
    result = asyncio.run(McpSandboxValidator().validate_mcp_server(
        str(candidate), McpCandidateContract("probe", "probe", "Disposable denial witness"),
    ))
    observer = subprocess.check_output(
        [sys.executable, "-c", "import pathlib,sys; print(pathlib.Path(sys.argv[1]).exists())", str(witness)],
        text=True,
    ).strip()
    source = root / "01_KISH_ENGINE/babylon60/kernel/mcp_sandbox_validator.py"
    print(json.dumps({"result": result, "outside_write_observed_by_other_process": observer,
                      "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                      "scope": "One real denial attempt; temporary filesystem and loopback witnesses only"}, indent=2))
    assert observer == "False", "The sandbox path allowed the outside fixture write"
    assert result["is_valid"] is False
    assert "Confined MCP exited 73: DENIAL errno=" in str(result["reason"])
