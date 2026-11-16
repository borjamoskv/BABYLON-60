#!/usr/bin/env python3
"""Audit gate enforcement using disposable resources; never authenticate or publish.

Run with Python 3.11+, Git, uv, Rust and this workspace's locked environment.
Software signatures in the selected tests are fixtures, not hardware attestation.
Remote inspection is read-only and opt-in with --remote.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time


SOURCES = (
    ".babylon60rules", ".pre-commit-config.yaml", "Cargo.lock", "uv.lock",
    ".github/workflows/ci.yml", ".github/workflows/production-deploy.yml",
    ".github/workflows/pypi-publish.yml", ".github/workflows/crates-publish.yml",
    ".github/workflows/oidc-deploy.yml", "scripts/guards/verify_publish_run.py",
    "scripts/guards/verify_active_topology.py", "scripts/c5_git_utils/c5_ship.sh",
    "scripts/c5_quality_gates/audit_semantic_contracts.py",
    "scripts/c5_quality_gates/audit_token_budget.py",
    "src/executor.rs", "src/secure_fs.rs", "src/tamkarum.rs", "src/bin/tamkarum.rs",
    "src/manifest.rs", "src/shared_manifest_core.rs", "src/halt.rs",
    "01_KISH_ENGINE/babylon60/mcp/effect_dispatch.py",
    "01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py",
    "01_KISH_ENGINE/babylon60/verification/verification_gate.py",
    "01_KISH_ENGINE/babylon60/verification/hardware_attestation.py",
    "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift",
    "tests/test_governance_gates.py", "tests/test_instruction_gate_regressions.py",
    "tests/test_semantic_contracts_gate.py", "tests/test_audit_release_gates.py",
    "tests/test_causal_hitl_verification_gate.py", "tests/test_fl_mcp01_dispatch.py",
    "tests/test_biometric_signing_contract.py", "tests/test_swarm100_lot3_regressions.py",
    "src/executor_tests.rs", "tests/fl_mcp01_authority_drift.rs",
    "tests/a02_effect_authorization.rs", "src/worm.rs", "tests/unit_tests.rs",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parents[4])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--remote", action="store_true")
    args = parser.parse_args()
    root = args.root.absolute()
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    sources = sorted(set(SOURCES) | {
        str(path.relative_to(root)) for path in (root / ".github/workflows").glob("*.yml")
    } | {str(Path(__file__).absolute().relative_to(root))})
    original = {name: digest(root / name) for name in sources}

    def run(name: str, command: list[str], *, cwd: Path = root,
            env: dict[str, str] | None = None, stdin: str | None = None,
            expected: int | str | None = None, timeout: int = 600,
            no_core_dump: bool = False) -> dict[str, object]:
        print(f"RUN {name}", flush=True)
        started = time.monotonic()
        try:
            proc = subprocess.run(command, cwd=cwd, env=env, input=stdin,
                                  text=True, capture_output=True, timeout=timeout, check=False,
                                  preexec_fn=(lambda: resource.setrlimit(resource.RLIMIT_CORE, (0, 0)))
                                  if no_core_dump else None)
            code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr = 124, str(exc.stdout or ""), str(exc.stderr or "")
        except OSError as exc:
            code, stdout, stderr = 127, "", str(exc)
        log = output / f"{len(results):02d}-{name}.log"
        log.write_text(f"exit_code={code}\nSTDOUT\n{stdout}\nSTDERR\n{stderr}")
        passed = None if expected is None else (code != 0 if expected == "nonzero" else code == expected)
        test_count = sum(int(count) for count in re.findall(r"(\d+) passed", stdout))
        if name.endswith("-tests") and code == 0 and test_count == 0:
            passed = False  # A filtered-out suite is not verification evidence.
        row = {"name": name, "argv": command, "cwd": str(cwd),
               "exit_code": code, "expected": expected, "expectation_met": passed,
               "passed_tests": test_count if name.endswith("-tests") else None,
               "seconds": round(time.monotonic() - started, 3), "log": log.name}
        results.append(row)
        print(f"RESULT {name}: rc={code}, expectation={passed}", flush=True)
        return row

    run("git-head", ["git", "rev-parse", "HEAD"], expected=0)
    run("git-status", ["git", "status", "--porcelain=v1", "--untracked-files=no"], expected=0)
    run("git-version", ["git", "--version"], expected=0)
    run("rust-version", ["rustc", "--version"], expected=0)
    run("uv-version", ["uv", "--version"], expected=0)
    hook_config = subprocess.run(["git", "config", "--get", "core.hooksPath"], cwd=root,
                                 text=True, capture_output=True, check=False)
    hooks = Path(hook_config.stdout.strip()) if hook_config.returncode == 0 else root / ".git/hooks"
    if not hooks.is_absolute():
        hooks = root / hooks
    hook_evidence = {}
    for hook_name in ("pre-commit", "pre-push"):
        hook = hooks / hook_name
        hook_evidence[hook_name] = {
            "path": str(hook), "exists": hook.is_file(),
            "sha256": digest(hook) if hook.is_file() else None,
            "source": hook.read_text() if hook.is_file() else None,
        }
    # Read only the explicit delegates already named in the effective hooks.
    for hook_name in ("pre-commit", "pre-push"):
        delegate = Path.home() / ".git_hooks" / hook_name
        if delegate.is_file() and str(delegate) in str(hook_evidence[hook_name]["source"]):
            hook_evidence[f"delegate-{hook_name}"] = {
                "path": str(delegate), "sha256": digest(delegate), "source": delegate.read_text(),
            }
    (output / "effective-hooks.json").write_text(json.dumps(hook_evidence, indent=2) + "\n")

    with tempfile.TemporaryDirectory(prefix="b60-gates-audit-") as temporary:
        fixture = Path(temporary)
        git_env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_AUTHOR_NAME="Gate audit fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                       GIT_COMMITTER_NAME="Gate audit fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            git_env.pop(key, None)
        repo = fixture / "repo"
        repo.mkdir()
        run("fixture-init", ["git", "init", "-q"], cwd=repo, env=git_env, expected=0)
        verifier = repo / "scripts/guards/verify_active_topology.py"
        verifier.parent.mkdir(parents=True)
        shutil.copyfile(root / "scripts/guards/verify_active_topology.py", verifier)
        active = hooks / "pre-commit"
        if active.is_file():
            installed = repo / ".git/hooks/pre-commit"
            shutil.copyfile(active, installed)
            installed.chmod(0o700)
            (repo / "witness.txt").write_text("disposable commit witness\n")
            run("fixture-stage", ["git", "add", "witness.txt"], cwd=repo, env=git_env, expected=0)
            run("actual-hook-rejects-missing-topology", ["git", "-c", "commit.gpgsign=false", "commit", "-qm", "fixture"],
                cwd=repo, env=git_env, expected="nonzero")
            run("fixture-no-verify-commits", ["git", "-c", "commit.gpgsign=false", "commit", "--no-verify", "-qm", "fixture"],
                cwd=repo, env=git_env, expected=0)
            run("fixture-independent-commit-observer", ["git", "show", "HEAD:witness.txt"],
                cwd=repo, env=git_env, expected=0)
            (repo / "second.txt").write_text("hooks disabled only in this temporary repository\n")
            run("fixture-stage-second", ["git", "add", "second.txt"], cwd=repo, env=git_env, expected=0)
            empty = fixture / "empty-hooks"
            empty.mkdir()
            run("fixture-hooks-path-override-commits",
                ["git", "-c", f"core.hooksPath={empty}", "-c", "commit.gpgsign=false", "commit", "-qm", "fixture two"],
                cwd=repo, env=git_env, expected=0)
        # A staged syntax error repaired only in the worktree is invisible to
        # the current global AST delegate, which compiles the worktree pathname.
        delegate = Path.home() / ".git_hooks/pre-commit"
        if delegate.is_file() and str(delegate) in str(hook_evidence["pre-commit"]["source"]):
            (repo / "syntax_fixture.py").write_text("def broken(:\n")
            run("fixture-stage-invalid-python", ["git", "add", "syntax_fixture.py"], cwd=repo, env=git_env, expected=0)
            (repo / "syntax_fixture.py").write_text("answer = 42\n")
            run("global-ast-delegate-accepts-staged-syntax-error", [str(delegate)], cwd=repo, env=git_env, expected=0)
            blob = subprocess.check_output(["git", "show", ":syntax_fixture.py"], cwd=repo, env=git_env, text=True)
            run("staged-python-independent-compiler", [sys.executable, "-c", "import sys; compile(sys.stdin.read(), 'staged', 'exec')"],
                cwd=repo, env=git_env, stdin=blob, expected="nonzero")

        harness = fixture / "budget.rs"
        # Both actual source modules are compiled unchanged, without mocks.
        harness.write_text(
            f"#[path = {json.dumps(str(root / 'src/manifest.rs'))}] mod manifest;\n"
            f"#[path = {json.dumps(str(root / 'src/tamkarum.rs'))}] mod tamkarum;\n"
            + """use tamkarum::{BudgetVerdict, KudurruBudgetGate};
fn main() {
    let mut gate = KudurruBudgetGate::new(10, 10, 250, [0; 32]);
    assert!(matches!(gate.evaluate_bid(10, 1, 1), BudgetVerdict::Allowed { .. }));
    assert!(matches!(gate.evaluate_bid(1, 1, 1), BudgetVerdict::ExceedsDailyBudget { .. }));
    gate.spent_today_cents = 0;
    assert!(matches!(gate.evaluate_bid(10, 1, 1), BudgetVerdict::Allowed { .. }));
    gate.consecutive_underperforming_epochs = 60;
    assert!(matches!(gate.evaluate_bid(1, 1, 1), BudgetVerdict::ApoptosisHalt { .. }));
    gate.consecutive_underperforming_epochs = 0;
    gate.spent_today_cents = 0;
    assert!(matches!(gate.evaluate_bid(1, 1, 1), BudgetVerdict::Allowed { .. }));
    println!("zero_attestation_accepted=true; budget_rejection=true; public_reset_restores_allow=true; halt_is_return_value=true");
    let shared = manifest::SharedManifest::new();
    assert!(shared.publish(1, &[1; 4]).is_ok());
    assert_eq!(shared.freeze(), Ok(1));
    assert!(shared.publish(2, &[2; 4]).is_err());
    assert!(shared.read().is_none());
    shared.seq.store(2, std::sync::atomic::Ordering::Release);
    shared.status_flag.store(manifest::RUNNING, std::sync::atomic::Ordering::Release);
    assert!(shared.publish(2, &[2; 4]).is_ok());
    println!("manifest_api_rejects_after_freeze=true; same_address_space_public_reset_restores_publish=true");
}
""")
        run("compile-actual-budget-module", ["rustc", "--edition=2021", "-Awarnings", str(harness), "-o", str(fixture / "budget")], expected=0)
        run("budget-no-attestation-and-reset-witness", [str(fixture / "budget")], expected=0)

    sha = "a" * 40
    good = {"headSha": sha, "status": "completed", "conclusion": "success", "event": "push", "headBranch": "main"}
    cases = [("valid", [good], 0), ("missing", [], "nonzero"), ("duplicate", [good, good], "nonzero")]
    for field, value in (("headSha", "b" * 40), ("status", "in_progress"),
                         ("conclusion", "failure"), ("conclusion", "cancelled"),
                         ("event", "pull_request"), ("headBranch", "feature")):
        cases.append((f"{field}-{value}", [dict(good, **{field: value})], "nonzero"))
    for name, payload, expected in cases:
        run(f"publish-validator-{name}", [sys.executable, "scripts/guards/verify_publish_run.py"],
            env=dict(os.environ, GITHUB_SHA=sha), stdin=json.dumps(payload), expected=expected)

    run("topology-self-test", [sys.executable, "scripts/guards/verify_active_topology.py", "--self-test"], expected=0)
    # These are observations of the dirty workspace, not assumptions of success.
    for name, command in (
        ("semantic-workspace", [sys.executable, "scripts/c5_quality_gates/audit_semantic_contracts.py", "--workspace-only"]),
        ("budget-workspace", [sys.executable, "scripts/c5_quality_gates/audit_token_budget.py", "--workspace-only", "--skip-ghost-listeners"]),
        ("topology-workspace", [sys.executable, "scripts/guards/verify_active_topology.py"]),
        ("topology-index", [sys.executable, "scripts/guards/verify_active_topology.py", "--staged"]),
    ):
        run(name, command)

    run("native-build", ["cargo", "build", "-q", "--locked", "-p", "babylon60_root", "--lib", "--features", "python"], expected=0)
    suffix = "dylib" if sys.platform == "darwin" else "so"
    library = root / f"target/debug/libbabylon60.{suffix}"
    test_env = dict(os.environ, BABYLON60_TEST_CAPABILITY_LIBRARY=str(library))
    suite = [
        "tests/test_governance_gates.py", "tests/test_instruction_gate_regressions.py",
        "tests/test_semantic_contracts_gate.py", "tests/test_audit_release_gates.py",
        "tests/test_causal_hitl_verification_gate.py", "tests/test_fl_mcp01_dispatch.py",
        "tests/test_biometric_signing_contract.py",
        "tests/test_swarm100_lot3_regressions.py",
    ]
    run("python-rejection-and-dispatch-tests", ["uv", "run", "--locked", "pytest", *suite,
        "-k", "not hardware_attested_fixture_effect", "-q"], env=test_env, expected=0)
    run("rust-executor-rejection-tests", ["cargo", "test", "-q", "--locked", "-p", "babylon60_root",
        "--lib", "executor::", "--", "--test-threads=1"], expected=0)
    run("rust-secure-fs-tests", ["cargo", "test", "-q", "--locked", "-p", "babylon60_root",
        "--lib", "secure_fs::tests", "--", "--test-threads=1"], expected=0)
    run("rust-mcp-authority-tests", ["cargo", "test", "-q", "--locked", "-p", "babylon60_root",
        "--test", "fl_mcp01_authority_drift", "--test", "a02_effect_authorization",
        "--", "--test-threads=1"], expected=0)
    run("rust-worm-integrity-tests", ["cargo", "test", "-q", "--locked", "-p", "babylon60_root",
        "--lib", "worm::tests", "--", "--test-threads=1"], expected=0)
    run("legacy-irreversibility-test-passes", ["cargo", "test", "-q", "--locked", "-p", "babylon60_root",
        "--test", "unit_tests", "inv4_poison_is_irreversible", "--", "--test-threads=1"], expected=0)

    # Link the real default-feature crate and observe SIGABRT in a disposable
    # child. An impossible receipt path tests termination despite I/O failure.
    run("default-native-build", ["cargo", "build", "-q", "--locked", "-p", "babylon60_root", "--lib"], expected=0)
    with tempfile.TemporaryDirectory(prefix="b60-halt-audit-") as temporary:
        fixture = Path(temporary)
        source = fixture / "halt_probe.rs"
        source.write_text("""fn main() {
    let shared = babylon60::SharedManifest::new();
    babylon60::halt::epistemic_halt(&shared, babylon60::HaltReason::ExternalSignal);
}
""")
        binary = fixture / "halt_probe"
        run("compile-real-halt-probe", ["rustc", "--edition=2021", str(source),
            "--extern", f"babylon60={root / 'target/debug/libbabylon60.rlib'}",
            "-L", f"dependency={root / 'target/debug/deps'}", "-o", str(binary)], expected=0)
        run("real-halt-aborts-despite-receipt-io-failure", [str(binary)], cwd=fixture,
            env=dict(os.environ, BABYLON_HALT_RECEIPT_PATH=str(fixture / "missing/receipt.cbor"),
                     BABYLON_HALT_EVIDENCE_BUDGET_MS="100"),
            expected=-signal.SIGABRT, timeout=10, no_core_dump=True)

    if args.remote:
        for name, endpoint in (
            ("main-protection", "branches/main/protection"),
            ("main-rules", "rules/branches/main"),
            ("production-environment", "environments/Production"),
        ):
            run(name, ["gh", "api", f"repos/borjamoskv/BABYLON-60-VAULT/{endpoint}"], timeout=60)

    changed = [name for name in sources if digest(root / name) != original[name]]
    evidence = {
        "audit_date_client": "2026-10-29", "root": str(root),
        "source_sha256": original, "source_files_changed_during_run": changed,
        "results": results,
        "unexpected_results": [r["name"] for r in results if r["expectation_met"] is False],
        "limits": ["No live biometric authentication or hardware provenance claim",
                   "No production effects, network publication, or configuration changes",
                   "Remote 403/404 are observations, not proof of effective protection",
                   "Host telemetry omitted; source hashes identify the dirty working tree",
                   "Returned DENY is distinguished from an effect that already started"],
    }
    (output / "results.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"results": str(output / "results.json"),
                      "unexpected_results": evidence["unexpected_results"], "changed_sources": changed}), flush=True)
    return int(bool(evidence["unexpected_results"] or changed))


if __name__ == "__main__":
    raise SystemExit(main())
