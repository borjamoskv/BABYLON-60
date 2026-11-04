"""Exercise the workflow's pipeline with an isolated scanner fixture."""

from pathlib import Path
import shutil
import subprocess

import pytest
import yaml


@pytest.mark.parametrize("scanner_exit", [0, 42])
def test_existence_gate_preserves_scanner_exit(tmp_path: Path, scanner_exit: int) -> None:
    workflow_path = Path(__file__).absolute().parents[1] / ".github/workflows/existence_gap_gate.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    job = workflow["jobs"]["existence-gap"]
    step = next(step for step in job["steps"] if step.get("id") == "scan")
    assert workflow["jobs"]["sast"]["needs"] == "existence-gap"
    shell = step.get("shell", job.get("defaults", {}).get("run", {}).get("shell"))
    if shell is None:
        shell = workflow.get("defaults", {}).get("run", {}).get("shell")
    # GitHub's documented Linux commands differ for omitted and explicit bash.
    assert shell in (None, "bash"), "Update the harness for this runner shell"
    bash = shutil.which("bash")
    assert bash is not None, "bash is required to exercise this Linux CI gate"
    options = ["--noprofile", "--norc", "-eo", "pipefail"] if shell == "bash" else ["-e"]
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    # Synthetic scanner only in this temporary checkout; no production scanner runs.
    (tools_dir / "existence_gap.py").write_text(
        f"print('isolated scanner report')\nraise SystemExit({scanner_exit})\n",
        encoding="utf-8",
    )
    script = tmp_path / "step.sh"
    script.write_text(step["run"] + "\necho reached-after-gate\n", encoding="utf-8")
    result = subprocess.run(
        [bash, *options, str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == scanner_exit, result.stdout + result.stderr
    assert (tmp_path / "existence-gap.txt").read_text(encoding="utf-8") == "isolated scanner report\n"
    assert ("reached-after-gate" in result.stdout) == (scanner_exit == 0)
