"""The committed source projection and the final wheel must serve a pinned MCP catalog."""

import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from babylon60.mcp.skills_snapshot import ImmutableSkillsSnapshot


@pytest.mark.parametrize("lock_path", ["skills-lock.json", "docs/skills-lock.json"])
def test_public_projection_matches_each_distributed_pin(lock_path: str) -> None:
    root = Path(__file__).absolute().parents[1]
    snapshot = ImmutableSkillsSnapshot.load(
        root / "docs/skills.json",
        root / ".agents/skills",
        lockfile_path=root / lock_path,
    )
    assert snapshot.to_lockfile() == json.loads((root / lock_path).read_text())
    assert (root / "skills-lock.json").read_bytes() == (root / "docs/skills-lock.json").read_bytes()


def test_final_wheel_initializes_and_lists_tools_outside_checkout(tmp_path: Path) -> None:
    wheel_path = os.environ.get("BABYLON60_TEST_WHEEL")
    if wheel_path is None:
        pytest.skip("set BABYLON60_TEST_WHEEL to exercise the final built wheel")
    wheel = Path(wheel_path).absolute()
    assert wheel.is_file(), f"Missing final wheel: {wheel}"
    package_root = tmp_path / "unpacked-wheel"
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(package_root)
    outside = tmp_path / "outside checkout"
    outside.mkdir()
    # PYTHONPATH takes priority over an editable checkout. The child asserts its origin too.
    env = os.environ.copy()
    env["PYTHONPATH"] = str(package_root)
    env["BABYLON_HOME"] = str(outside / "state")
    code = (
        "from pathlib import Path; "
        "import babylon60.mcp.cortex_mcp_server as server; "
        f"assert Path(server.__file__).is_relative_to(Path({str(package_root)!r})); "
        "server.main()"
    )
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            "--ledger",
            str(outside / "ledger.db"),
            "--causal-gate",
            str(outside / "causal.db"),
        ],
        input="".join(json.dumps(request) + "\n" for request in requests),
        cwd=outside,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    responses = [json.loads(line) for line in result.stdout.splitlines()]
    assert [response["id"] for response in responses] == [1, 2]
    assert responses[0]["result"]["serverInfo"]["name"] == "cortex-persist-bft"
    assert "bft_query_ledger" in {tool["name"] for tool in responses[1]["result"]["tools"]}
