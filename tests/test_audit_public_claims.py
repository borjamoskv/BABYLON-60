"""Document contracts, checked without launching hardware benchmarks."""

from pathlib import Path
import re
import subprocess
import sys
import tomllib
from urllib.parse import unquote, urlsplit

import pytest

from scripts.c5_quality_gates.governance_documents import validate_local_links

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("option", "expected_exit"), [("--help", 0), ("-h", 0), ("--unknown-option", 2), ("--run-invariants", 2)]
)
def test_claim_verifier_help_and_unknown_options_never_run_suites(monkeypatch, capsys, option, expected_exit):
    from scripts.c5_quality_gates import verify_claims

    monkeypatch.setattr(sys, "argv", ["verify_claims.py", option])

    def forbid_suite(*args, **kwargs):
        pytest.fail("help or an invalid option must not start claim verification")

    monkeypatch.setattr(verify_claims, "source_commit", forbid_suite)
    monkeypatch.setattr(verify_claims, "run_command", forbid_suite)
    with pytest.raises(SystemExit) as exc:
        verify_claims.main()
    assert exc.value.code == expected_exit
    stdout, stderr = capsys.readouterr()
    assert "usage:" in (stdout if expected_exit == 0 else stderr)


@pytest.mark.parametrize(
    "options",
    [
        ["--list", "--check-invariants"],
        ["--check-invariants", "--list"],
        ["--list", "--check-invariants", "--run-invariants"],
    ],
)
def test_claim_verifier_rejects_ambiguous_modes(monkeypatch, options):
    from scripts.c5_quality_gates import verify_claims

    monkeypatch.setattr(sys, "argv", ["verify_claims.py", *options])
    monkeypatch.setattr(verify_claims, "source_commit", lambda *args: pytest.fail("must not execute"))
    with pytest.raises(SystemExit) as exc:
        verify_claims.main()
    assert exc.value.code == 2


@pytest.mark.parametrize(
    ("options", "expected_exit"),
    [
        (["--help"], 0),
        (["--help", "--execute"], 0),
        (["--execute", "--help"], 0),
        (["--unknown", "--execute"], 2),
        (["--exec"], 2),
        (["--list", "--execute"], 2),
        (["--execute", "--list"], 2),
        (["--list", "--strict"], 2),
        (["--strict", "--list"], 2),
    ],
)
def test_claim_wrapper_help_and_unknown_options_never_run_suites(monkeypatch, capsys, options, expected_exit):
    from scripts import verify_claims

    monkeypatch.setattr(sys, "argv", ["verify_claims.py", *options])

    def forbid_suite(*args, **kwargs):
        pytest.fail("help or an invalid option must not start claim verification")

    monkeypatch.setattr(subprocess, "run", forbid_suite)
    with pytest.raises(SystemExit) as exc:
        verify_claims.main()
    assert exc.value.code == expected_exit
    stdout, stderr = capsys.readouterr()
    assert "usage:" in (stdout if expected_exit == 0 else stderr)


@pytest.mark.parametrize(
    "options", [["--check-invariants", "--run-invariants"], ["--run-invariants", "--check-invariants"]]
)
def test_claim_invariant_runner_accepts_explicit_check_mode(monkeypatch, options):
    from scripts.c5_quality_gates import verify_claims

    monkeypatch.setattr(sys, "argv", ["verify_claims.py", *options])
    calls = []
    monkeypatch.setattr(verify_claims, "execute_invariant_suites", lambda *args: calls.append(args))
    assert verify_claims.main() == 0
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("options", "list_only"), [([], True), (["--list"], True), (["--execute"], False), (["--strict"], False)]
)
def test_claim_wrapper_modes_are_preserved(monkeypatch, options, list_only):
    from scripts import verify_claims

    monkeypatch.setattr(sys, "argv", ["verify_claims.py", *options])
    calls = []

    def record_run(command):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", record_run)
    assert verify_claims.main() == 0
    assert len(calls) == 1
    assert ("--list" in calls[0]) is list_only


def test_energy_claim_is_scoped_and_compatible_with_listing():
    claim = tomllib.loads((ROOT / "CLAIMS.toml").read_text())["claim"]["zero_anergy"]
    assert claim["status"] == "partial_trace"
    assert claim["evidence_level"] == "L2_IMPLEMENTATION"
    assert "does not measure RFO" in claim["statement"]
    assert "NO_VERIFICADO" in claim["notes"]
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/c5_quality_gates/verify_claims.py"), "--list"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "[DECLARED] zero_anergy" in result.stdout
    assert "No outcome asserted" in result.stdout


# README.md is the English front page and README_ES.md its Spanish translation;
# both link to the same scoped technical contract, each in its own language.
README_CONTRACTS = {
    "README.md": {
        "reference": "docs/03_guides/README_REFERENCE.md",
        "faq_heading": "Frequently Asked Questions",
        "no_fallback": "no retries and no fallback authentication",
        "hash_matrix": "Normative Hash Matrix (`BLAKE3` · `SHA-256` · `SHA3-256`)",
        "legacy_wal": "`SHA-256` over the first 122 bytes",
        "incident_bounds": "Incident Bounds (Process `SIGKILL` vs. Physical Power Loss)",
    },
    "README_ES.md": {
        "reference": "docs/03_guides/README_REFERENCE_ES.md",
        "faq_heading": "Preguntas Frecuentes para Humanos",
        "no_fallback": "sin reintentos ni autenticación alternativa",
        "hash_matrix": "Matriz Normativa de Hashes (`BLAKE3` · `SHA-256` · `SHA3-256`)",
        "legacy_wal": "`SHA-256` sobre los primeros 122 bytes",
        "incident_bounds": "Cotas de Incidentes (`SIGKILL` de Proceso vs. Corte Eléctrico Físico)",
    },
}


@pytest.mark.parametrize("readme", sorted(README_CONTRACTS))
def test_faq_does_not_promise_authentication_fallback_or_zero_energy(readme):
    contract = README_CONTRACTS[readme]
    faq = (ROOT / readme).read_text(encoding="utf-8").split(contract["faq_heading"], 1)[1]
    assert contract["no_fallback"] in faq
    assert "NO_VERIFICADO" in faq
    for promise in ("conmuta automáticamente", "switches automatically", "0.00%", "($RFO=0$)"):
        assert promise not in faq


def test_normative_hash_matrix_and_incident_bounds_declared():
    manifest = tomllib.loads((ROOT / "CLAIMS.toml").read_text())
    metadata = manifest["metadata"]
    assert "BLAKE3_CANONICAL" in metadata["hash_matrix_normative"]
    assert "SHA256_HARDWARE_AND_WITNESS" in metadata["hash_matrix_normative"]
    assert "SHA3_256_LEGACY_L0" in metadata["hash_matrix_normative"]
    assert "SIGKILL_VERIFIED" in metadata["incident_bounds_normative"]
    assert "POWER_LOSS_UNVERIFIED" in metadata["incident_bounds_normative"]

    sqlite_claim = manifest["claim"]["cortex_persist_sqlite"]
    assert "The normative BLAKE3 profile" in sqlite_claim["notes"]
    assert "SHA-256 Hardware/Witness" in sqlite_claim["notes"]
    assert "SHA3-256 Legacy L0" in sqlite_claim["notes"]
    assert "SIGKILL" in sqlite_claim["scope"]
    assert "corte eléctrico" in sqlite_claim["scope"]

    for readme, contract in README_CONTRACTS.items():
        readme_text = (ROOT / readme).read_text(encoding="utf-8")
        reference = contract["reference"]
        assert f"]({reference}#" in readme_text, readme
        reference_text = (ROOT / reference).read_text(encoding="utf-8")
        assert contract["hash_matrix"] in reference_text, reference
        assert "SHA256_LEGACY_EFFECT_WAL" in reference_text, reference
        assert contract["legacy_wal"] in reference_text, reference
        assert contract["incident_bounds"] in reference_text, reference

    why_text = (ROOT / "WHY_BABYLON_60.md").read_text()
    assert "registros legados de 154 bytes en `.effect_wal.bin` (`SHA-256` sobre los primeros 122 bytes)" in why_text


def test_monorepo_readmes_have_valid_local_links_and_no_legacy_packages_paths():
    entry_documents = [ROOT / name for name in README_CONTRACTS]
    references = [ROOT / contract["reference"] for contract in README_CONTRACTS.values()]
    assert validate_local_links(entry_documents + references) == []
    readmes = [
        "README.md",
        "README_ES.md",
        "docs/03_guides/README_REFERENCE.md",
        "docs/03_guides/README_REFERENCE_ES.md",
        "docs/README.md",
        "src/README.md",
        "00_ABZU_KERNEL/README.md",
        "00_ABZU_KERNEL/crates/babylon60-kernel/README.md",
        "00_ABZU_KERNEL/crates/babylon60-compiler/README.md",
        "00_ABZU_KERNEL/crates/strike-rs/README.md",
        "crates/eridu-infer/README.md",
        "01_KISH_ENGINE/README.md",
        "01_KISH_ENGINE/babylon60/kernel/README.md",
        "01_KISH_ENGINE/babylon60/agents/sovereign_mcp/README.md",
        "02_EDIN_SWARMS/README.md",
        "proof/README.md",
        "tests/README.md",
        "tools/README.md",
    ]
    for rel in readmes:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        assert "PYTHONPATH=packages:." not in text, f"Obsolete PYTHONPATH=packages:. in {rel}"
        assert "packages/babylon60/" not in text, f"Obsolete packages/babylon60/ path in {rel}"
        for target in re.findall(r"\]\(([^)]+)\)", text):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            dest = (path.parent / unquote(parsed.path)).resolve()
            assert dest.exists(), f"Broken local link in {rel}: {target} -> {dest}"


def test_fl_aiact_02_claim_registered_with_explicit_non_certification_scope():
    manifest = tomllib.loads((ROOT / "CLAIMS.toml").read_text(encoding="utf-8"))
    claim = manifest["claim"]["FL_AIACT_02_regulatory_evidence_graph"]
    assert claim["status"] == "verified"
    assert claim["evidence_level"] == "L2_IMPLEMENTATION"
    assert "TechnicalPASS != LegalConformity" in claim["statement"]
    assert "Does not constitute or emit automatic EU AI Act legal conformity certification" in claim["scope"]
    assert "tests/test_fl_aiact_02_evidence_graph.py" in claim["evidence_suite"]


def test_invariants_aligned_between_claims_and_babylon_toml():
    listing = subprocess.run(
        [sys.executable, str(ROOT / "scripts/c5_quality_gates/verify_claims.py"), "--list"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "[INVARIANT] ax0_hardware_closure (CLAIM-AX0-HW-005)" in listing.stdout
    assert "[INVARIANT] lean4_observable_harness (CLAIM-FORMAL-008)" in listing.stdout
    assert "[INVARIANT] mcp_lifecycle_confinement (CLAIM-MCP-006)" in listing.stdout
    assert "[INVARIANT] kernel_ledger_and_sqlite_hygiene (CLAIM-L0-007)" in listing.stdout
    assert "[INVARIANT] semantic_entropy_and_solver (CLAIM-RING1-009)" in listing.stdout
    assert "No outcome asserted" in listing.stdout

    gate = subprocess.run(
        [sys.executable, str(ROOT / "scripts/c5_quality_gates/verify_claims.py"), "--check-invariants"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "PASS: 5 [invariants.*]" in gate.stdout


def test_audit_invariants_rejects_babylon_toml_overclaiming():
    import copy
    from scripts.c5_quality_gates.verify_claims import audit_invariants_alignment

    claims_doc = tomllib.loads((ROOT / "CLAIMS.toml").read_text(encoding="utf-8"))
    babylon_release = tomllib.loads((ROOT / "babylon.toml").read_text(encoding="utf-8"))["release"]

    records, errors = audit_invariants_alignment(claims_doc, babylon_release)
    assert len(records) == 5
    assert errors == []

    # 1. Live overclaiming: promoting CLAIM-MCP-006 in babylon.toml to VERIFIED while CLAIMS.toml is VERIFIED_LOCAL
    bad_live_mcp = copy.deepcopy(babylon_release)
    bad_live_mcp["gate_attestations"]["mcp_confinement"]["status"] = "VERIFIED"
    _, errs = audit_invariants_alignment(claims_doc, bad_live_mcp)
    assert any("mcp_confinement.status='VERIFIED'" in e for e in errs)

    # 2. Declaring VERIFIED or VERIFIED_LOCAL without an executable evidence_suite fails closed
    missing_suite_claims = copy.deepcopy(claims_doc)
    missing_suite_claims["invariants"]["kernel_ledger_and_sqlite_hygiene"].pop("evidence_suite", None)
    _, errs = audit_invariants_alignment(missing_suite_claims, babylon_release)
    assert any("evidence_suite ejecutable no vacío" in e for e in errs)

    # 3. Synthetic NO_VERIFICADO regression checks (preserving all overclaiming guards)
    unverified_claims = copy.deepcopy(claims_doc)
    unverified_claims["invariants"]["semantic_entropy_and_solver"]["status"] = "NO_VERIFICADO"
    unverified_claims["invariants"]["mcp_lifecycle_confinement"]["status"] = "NO_VERIFICADO"
    unverified_claims["invariants"]["kernel_ledger_and_sqlite_hygiene"]["status"] = "NO_VERIFICADO"

    unverified_rel = copy.deepcopy(babylon_release)
    unverified_rel["gate_attestations"]["semantic_entropy_solver"] = "NO_VERIFICADO"
    unverified_rel["gate_attestations"]["mcp_confinement"]["status"] = "NO_VERIFICADO"
    unverified_rel["gate_attestations"]["mcp_confinement"]["effect_tx_quarantine"] = "NO_VERIFICADO"
    unverified_rel["gate_attestations"]["storage_and_consensus"]["status"] = "NO_VERIFICADO"
    unverified_rel["gate_attestations"]["storage_and_consensus"]["sqlite_cortex_teardown"] = "NO_VERIFICADO"
    unverified_rel["gate_attestations"]["storage_and_consensus"]["ledger_idempotency"] = "VERIFIED_LOCAL"
    unverified_rel["gate_attestations"]["storage_and_consensus"]["atomic_file_writes"] = "VERIFIED_LOCAL"
    unverified_rel["gate_attestations"]["storage_and_consensus"]["bft_collision_barrier"] = "NO_VERIFICADO"
    assert audit_invariants_alignment(unverified_claims, unverified_rel)[1] == []

    bad_solver = copy.deepcopy(unverified_rel)
    bad_solver["gate_attestations"]["semantic_entropy_solver"] = "VERIFIED"
    _, errs = audit_invariants_alignment(unverified_claims, bad_solver)
    assert any("semantic_entropy_solver" in e for e in errs)

    bad_mcp = copy.deepcopy(unverified_rel)
    bad_mcp["gate_attestations"]["mcp_confinement"]["effect_tx_quarantine"] = "ACTIVE"
    bad_mcp["gate_attestations"]["mcp_confinement"]["token_replay_window"] = 0
    _, errs = audit_invariants_alignment(unverified_claims, bad_mcp)
    assert any("effect_tx_quarantine" in e for e in errs)
    assert any("token_replay_window" in e for e in errs)

    bad_l0 = copy.deepcopy(unverified_rel)
    bad_l0["gate_attestations"]["storage_and_consensus"]["bft_collision_barrier"] = "BftCollisionError"
    _, errs = audit_invariants_alignment(unverified_claims, bad_l0)
    assert any("bft_collision_barrier" in e for e in errs)


def test_babylon_toml_requires_candidate_state_while_required_invariants_are_unverified(tmp_path: Path) -> None:
    import copy
    from scripts.c5_quality_gates.verify_claims import audit_invariants_alignment

    claims_text = (ROOT / "CLAIMS.toml").read_text(encoding="utf-8")
    babylon_text = (ROOT / "babylon.toml").read_text(encoding="utf-8")
    claims_doc = tomllib.loads(claims_text)
    babylon_release = tomllib.loads(babylon_text)["release"]

    assert babylon_release["state"] == "candidate"

    # 1. Live repo: CLAIM-MCP-006 is VERIFIED_LOCAL (not hardware-attested in public tree), so stable state fails closed
    stable_release = copy.deepcopy(babylon_release)
    stable_release["state"] = "stable-terminal-mcp"
    _, errs = audit_invariants_alignment(claims_doc, stable_release)
    assert any("release.state='stable-terminal-mcp'" in e and "CLAIM-MCP-006" in e for e in errs)

    # Downgrading CLAIM-L0-007 or CLAIM-RING1-009 to NO_VERIFICADO also blocks stable state
    degraded_claims = copy.deepcopy(claims_doc)
    degraded_claims["invariants"]["kernel_ledger_and_sqlite_hygiene"]["status"] = "NO_VERIFICADO"
    degraded_claims["invariants"]["semantic_entropy_and_solver"]["status"] = "NO_VERIFICADO"
    _, degraded_errs = audit_invariants_alignment(degraded_claims, stable_release)
    assert any("CLAIM-L0-007" in e for e in degraded_errs)
    assert any("CLAIM-RING1-009" in e for e in degraded_errs)

    # 2. Missing babylon.toml [release] or empty gate_attestations must fail closed (never silently pass)
    _, missing_rel_errs = audit_invariants_alignment(claims_doc, None)
    assert any("[release] ausente" in e for e in missing_rel_errs)

    empty_gates = copy.deepcopy(babylon_release)
    empty_gates["gate_attestations"] = {}
    _, empty_gate_errs = audit_invariants_alignment(claims_doc, empty_gates)
    assert any("[release.gate_attestations] ausente o vacío" in e for e in empty_gate_errs)

    # 3. End-to-end subprocess check with --check-invariants on isolated fixture fails closed on stable state
    fixture = tmp_path / "repo"
    (fixture / "scripts" / "c5_quality_gates").mkdir(parents=True)
    verifier_copy = fixture / "scripts" / "c5_quality_gates" / "verify_claims.py"
    verifier_copy.write_text(
        (ROOT / "scripts/c5_quality_gates/verify_claims.py").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (fixture / "CLAIMS.toml").write_text(claims_text, encoding="utf-8")
    (fixture / "babylon.toml").write_text(
        babylon_text.replace('state = "candidate"', 'state = "stable-terminal-mcp"', 1),
        encoding="utf-8",
    )
    res = subprocess.run(
        [sys.executable, str(verifier_copy), "--check-invariants"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 1
    assert "[FAIL-CLOSED]" in res.stderr
    assert "stable-terminal-mcp" in res.stderr
