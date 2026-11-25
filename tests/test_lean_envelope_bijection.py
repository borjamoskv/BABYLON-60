"""Compile byte-level proofs with the project pin and compare independent encoders."""

import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest
import yaml


ROOT = Path(__file__).absolute().parents[1]
LEAN = ROOT / "proof/lean"
PIN = (LEAN / "lean-toolchain").read_text().strip()


def run(command, *, env=None, check=True):
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
    if check:
        assert result.returncode == 0, result.stdout + result.stderr
    return result


@pytest.fixture(scope="module")
def compiled(tmp_path_factory):
    if shutil.which("elan") is None:
        if os.environ.get("BABYLON60_REQUIRE_LEAN_ENVELOPES") == "1":
            pytest.fail("The required Lean envelope verification needs elan")
        pytest.skip("Lean unavailable; verify_lean workflow checks envelope proofs mandatorily")
    directory = tmp_path_factory.mktemp("lean-envelope-oleans")
    env = dict(os.environ, LEAN_PATH=str(directory))
    for name in ("CanonicalHead", "CanonicalEnvelope", "TicketEnvelope", "AcsEnvelope"):
        source = LEAN / f"{name}.lean"
        assert source.is_file()
        assert not re.search(r"\b(?:sorry|admit|axiom)\b", source.read_text())
        run(["elan", "run", PIN, "lean", "-o", str(directory / f"{name}.olean"), str(source)], env=env)
    return env


def vectors(output, prefix):
    return dict(re.findall(rf"^{prefix}([A-Za-z_0-9]+)=([0-9a-f]+)$", output, re.M))


def test_pinned_lean_ticket_encoding_matches_rust(compiled):
    lean = run(["elan", "run", PIN, "lean", "--run", str(LEAN / "TicketEnvelope.lean")], env=compiled)
    rust = run(
        [
            "cargo",
            "test",
            "--locked",
            "-p",
            "babylon60_root",
            "--lib",
            "omega_mediation::trusted_dispatch_tests::export_lean_ticket_vectors",
            "--",
            "--ignored",
            "--exact",
            "--nocapture",
        ]
    )
    actual = vectors(lean.stdout, "TICKET_")
    expected = vectors(rust.stdout, "TICKET_")
    assert set(expected) == {"CLI", "AX", "EDGE"}
    assert actual == expected


def test_pinned_lean_acs_encoding_matches_rust(compiled):
    rust = run(
        [
            "cargo",
            "test",
            "--locked",
            "-p",
            "babylon60_root",
            "--test",
            "acs_authenticated",
            "lean_golden_vectors_match_runtime_encoder",
            "--",
            "--exact",
        ]
    )
    assert re.search(r"test result: ok\. 1 passed;", rust.stdout), rust.stdout
    result = run(["elan", "run", PIN, "lean", "--run", str(LEAN / "AcsEnvelope.lean")], env=compiled)
    fixture = dict(line.split() for line in (ROOT / "tests/acs_cbor_golden.txt").read_text().splitlines())
    assert set(fixture) == {
        "root",
        "delegated",
        "grant",
        "call",
        "call_signing",
        "forensic",
        "forensic_signing",
        "cose_ed",
        "cose_p256",
    }
    actual = vectors(result.stdout, "ACS_")
    assert actual
    assert actual == fixture


def test_ticket_decoder_rejects_malformed_and_noncanonical(compiled):
    result = run(["elan", "run", PIN, "lean", "--run", str(LEAN / "TicketEnvelope.lean")], env=compiled)
    valid = vectors(result.stdout, "TICKET_")["CLI"]
    cases = ["", valid[:-2], valid + "00", "9f" + valid[2:] + "ff", "980d" + valid[2:], "00"]
    for encoded in cases:
        rejected = run(
            ["elan", "run", PIN, "lean", "--run", str(LEAN / "TicketEnvelope.lean"), "--decode", encoded],
            env=compiled,
            check=False,
        )
        assert rejected.returncode != 0, encoded
        assert "REJECT" in rejected.stdout, rejected.stdout + rejected.stderr


def test_acs_decoders_reject_truncation_and_trailing_bytes(compiled):
    fixture = dict(line.split() for line in (ROOT / "tests/acs_cbor_golden.txt").read_text().splitlines())
    for kind, name in [("call", "call"), ("grant", "grant"), ("forensic", "forensic"), ("cose-forensic", "cose_ed")]:
        command = ["elan", "run", PIN, "lean", "--run", str(LEAN / "AcsEnvelope.lean"), f"--decode-{kind}"]
        valid = fixture[name]
        run([*command, valid], env=compiled)
        for malformed in [valid[:-2], valid + "00"]:
            result = run([*command, malformed], env=compiled, check=False)
            assert result.returncode == 1, (kind, malformed)
            assert not result.stdout.strip() and not result.stderr.strip(), result.stdout + result.stderr


def test_ci_requires_cross_language_regression_without_skip():
    workflow = yaml.load((ROOT / ".github/workflows/verify_lean.yml").read_text(), Loader=yaml.BaseLoader)
    steps = workflow["jobs"]["verify-lean"]["steps"]
    checks = [step for step in steps if "pytest tests/test_lean_envelope_bijection.py" in step.get("run", "")]
    assert len(checks) == 1
    check = checks[0]
    assert check["env"]["BABYLON60_REQUIRE_LEAN_ENVELOPES"] == "1"
    assert check["working-directory"] == "${{ github.workspace }}"
    assert "--locked" in check["run"]
    assert check.get("continue-on-error", "false") == "false"
    assert "if" not in check
    for event in ("push", "pull_request"):
        paths = workflow["on"][event]["paths"]
        assert {
            "src/omega_mediation.rs",
            "src/acs_bridge.rs",
            "tests/acs_authenticated.rs",
            "tests/acs_cbor_golden.txt",
            "tests/test_lean_envelope_bijection.py",
        } <= set(paths)
