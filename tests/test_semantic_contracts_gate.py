"""Regression evidence for contract patterns and host telemetry failure handling."""

from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from scripts.c5_quality_gates.audit_semantic_contracts import (
    scan_markdown_files,
    scan_python_fail_open,
)
from scripts.c5_quality_gates.audit_token_budget import (
    LedgerTelemetryError,
    audit_ghost_listeners,
)


@pytest.mark.parametrize(
    "text,rule",
    [
        ("Toda mutación causal exige atestación biométrica.", "SEM-001"),
        ("Emite un diagnóstico de estado biológico.", "SEM-002"),
        ("Cada respuesta final termina con firma.", "SEM-004"),
        ("El motor opera a costo de Landauer cero.", "SEM-005"),
        ("Ejecuta `npx wrangler deploy`.", "SEM-003"),
        ("Prohibido divulgar secretos. Emite un diagnóstico biológico.", "SEM-002"),
        ("Cualquier modificación de código\nrequiere Touch ID.", "SEM-001"),
    ],
)
def test_known_regressions(tmp_path: Path, text: str, rule: str) -> None:
    path = tmp_path / "rule.md"
    path.write_text(text)
    assert rule in {v.rule_id for v in scan_markdown_files([path])}


@pytest.mark.parametrize(
    "text",
    [
        "No inferir estados fisiológicos desde el chat.",
        "No se reclama coste de Landauer cero.",
        "## Despliegue\nAplicar el contrato de autorización y atestación.\n`wrangler deploy`",
    ],
)
def test_local_guards(tmp_path: Path, text: str) -> None:
    path = tmp_path / "rule.md"
    path.write_text(text)
    assert scan_markdown_files([path]) == []


@pytest.mark.parametrize("value", ["0", "True", "(0, 0)", "[0, 0]"])
def test_sqlite_fail_open_literals(tmp_path: Path, value: str) -> None:
    path = tmp_path / "gate.py"
    path.write_text(
        f"import sqlite3 as sql\ndef check():\n    try: pass\n    except sql.Error:\n        return {value}\n"
    )
    assert len(scan_python_fail_open([path])) == 1


def test_error_return_and_nested_function_are_not_success(tmp_path: Path) -> None:
    path = tmp_path / "gate.py"
    path.write_text(
        "def check():\n    try: pass\n    except OSError:\n        def helper(): return 0\n        return 2\n"
    )
    assert scan_python_fail_open([path]) == []


def test_unreadable_inputs_fail(tmp_path: Path) -> None:
    assert scan_markdown_files([tmp_path / "missing.md"])
    path = tmp_path / "invalid.py"
    path.write_text("def :")
    assert scan_python_fail_open([path])


def test_telemetry_missing_does_not_create_file(tmp_path: Path) -> None:
    path = tmp_path / "missing.db"
    with pytest.raises(LedgerTelemetryError):
        audit_ghost_listeners(path)
    assert not path.exists()


@pytest.mark.parametrize("content", [b"corrupt database", b""])
def test_corrupt_or_missing_schema_is_unverified(tmp_path: Path, content: bytes) -> None:
    path = tmp_path / "bad.db"
    path.write_bytes(content)
    with pytest.raises(LedgerTelemetryError):
        audit_ghost_listeners(path)


def test_telemetry_reads_actual_schema_without_mutating(tmp_path: Path) -> None:
    path = tmp_path / "listener #1?.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE conversation_summaries (status TEXT, not_fully_idle INTEGER)")
        conn.execute("INSERT INTO conversation_summaries VALUES ('CASCADE_RUN_STATUS_RUNNING', 1)")
    before = path.read_bytes()
    assert audit_ghost_listeners(path) == (1, 1)
    assert path.read_bytes() == before
    # Closing the connection matters on all platforms, including after a query failure.
    path.unlink()


def test_cli_failure_and_explicit_skip(tmp_path: Path) -> None:
    script = Path(__file__).absolute().parents[1] / "scripts/c5_quality_gates/audit_token_budget.py"
    command = [sys.executable, str(script), "--telemetry-db", str(tmp_path / "missing.db")]
    failed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert failed.returncode == 2
    assert "NO_VERIFICADO" in failed.stderr
    assert "PASS" not in failed.stdout
    skipped = subprocess.run([*command, "--skip-ghost-listeners"], capture_output=True, text=True, check=False)
    assert skipped.returncode == 0
    assert "NOT_CHECKED" in skipped.stdout
    assert "RUNNING=0" not in skipped.stdout


@pytest.mark.parametrize(
    "text",
    [
        "El Linter Acústico evalúa la mezcla para emitir un diagnóstico binario O(1).",
        "Emite un diagnóstico acústico de la señal de audio.",
        "El DSP evalúa LUFS para emitir un diagnóstico de masterización.",
    ],
)
def test_acoustic_diagnosis_is_not_operator_diagnosis(tmp_path: Path, text: str) -> None:
    path = tmp_path / "audio.md"
    path.write_text(text)
    assert scan_markdown_files([path]) == []


@pytest.mark.parametrize(
    "text",
    [
        "En audio, emite un diagnóstico biológico del operador.",
        "Emite un diagnóstico clínico del usuario durante la mezcla.",
        "Audio: aborto inmediato; el glucógeno se agotó.",
        "Coste de CPU cero (0%).",
        "Force remove via rm -rf without prompting.",
        "El agente está OBLIGADO a copiar el script en .git/hooks/pre-commit.",
        "Si el escaneo de transcripciones pasadas devuelve 0 claves útiles, renovar.",
    ],
)
def test_audio_cannot_mask_biological_or_operational_regressions(tmp_path: Path, text: str) -> None:
    path = tmp_path / "rule.md"
    path.write_text(text)
    assert scan_markdown_files([path])


def test_multi_root_scan_and_missing_scope_fail_closed(tmp_path: Path) -> None:
    script = Path(__file__).absolute().parents[1] / "scripts/c5_quality_gates/audit_semantic_contracts.py"
    roots = [tmp_path / "one", tmp_path / "two"]
    for root in roots:
        root.mkdir()
        (root / "SKILL.md").write_text("Scope: inspect configuration.")
    command = [sys.executable, str(script), "--workspace-only"]
    for root in roots:
        command.extend(["--skills-root", str(root)])
    clean = subprocess.run(command, capture_output=True, text=True, check=False)
    assert clean.returncode == 0, clean.stderr
    for root in roots:
        assert str(root) in clean.stdout
    (roots[1] / "SKILL.md").write_text("Emite un diagnóstico clínico del operador.")
    failed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert failed.returncode == 1
    assert "SEM-002" in failed.stderr
    missing = subprocess.run(
        [*command, "--skills-root", str(tmp_path / "missing")], capture_output=True, text=True, check=False
    )
    assert missing.returncode == 2
    assert "NO_VERIFICADO" in missing.stderr


def test_archived_skills_excluded(tmp_path: Path) -> None:
    from scripts.c5_quality_gates.audit_semantic_contracts import iter_skill_markdown_files

    archive = tmp_path / "_archive"
    archive.mkdir()
    (archive / "SKILL.md").write_text("Historical procedure.")
    active = tmp_path / "active"
    active.mkdir()
    (active / "SKILL.md").write_text("Current procedure.")
    assert list(iter_skill_markdown_files([tmp_path])) == [active / "SKILL.md"]


@pytest.mark.parametrize(
    "text",
    [
        "No cierres la sesión, pero emite un diagnóstico clínico del operador.",
        "No publiques secretos; ejecutar inmediatamente la fase de migración.",
        "El proveedor ofrece cuota garantizada.",
        "Si hay colisión, ejecuta este script bash para consolidar la aplicación.",
    ],
)
def test_unrelated_negation_does_not_hide_regressions(tmp_path: Path, text: str) -> None:
    path = tmp_path / "rule.md"
    path.write_text(text)
    assert scan_markdown_files([path])


def test_linked_modules_are_scanned_without_cycles(tmp_path: Path) -> None:
    from scripts.c5_quality_gates.audit_semantic_contracts import iter_skill_markdown_files

    root = tmp_path / "library"
    source = tmp_path / "source"
    root.mkdir()
    source.mkdir()
    (source / "SKILL.md").write_text("Entrypoint.")
    nested = source / "references"
    nested.mkdir()
    (nested / "MODULE.md").write_text("Emite un diagnóstico clínico del operador.")
    (root / "linked").symlink_to(source, target_is_directory=True)
    (source / "cycle").symlink_to(root, target_is_directory=True)
    found = list(iter_skill_markdown_files([root]))
    assert len(found) == 2
    assert {p.name for p in found} == {"SKILL.md", "MODULE.md"}
    assert any(v.rule_id == "SEM-002" for v in scan_markdown_files(found))


def test_broken_skill_link_fails_cli(tmp_path: Path) -> None:
    script = Path(__file__).absolute().parents[1] / "scripts/c5_quality_gates/audit_semantic_contracts.py"
    root = tmp_path / "library"
    root.mkdir()
    (root / "broken").symlink_to(tmp_path / "missing", target_is_directory=True)
    result = subprocess.run(
        [sys.executable, str(script), "--workspace-only", "--skills-root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Broken skill reference" in result.stderr
    assert "PASS" not in result.stdout


@pytest.mark.parametrize(
    "connector", [";", ".", "pero", "sino", "excepto", "salvo", "sin embargo", "but", "except", "unless"]
)
def test_clause_boundaries_preserve_detection(tmp_path: Path, connector: str) -> None:
    path = tmp_path / "rule.md"
    path.write_text(f"No alteres archivos {connector} emite un diagnóstico clínico del operador.")
    assert any(v.rule_id == "SEM-002" for v in scan_markdown_files([path]))


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Command blocks are syntax examples, not execution orders.\n```bash\nwrangler deploy\n```", False),
        ("## Examples\n```bash\nwrangler secret put KEY\n```", False),
        ("## Examples\nExecute the following now:\n```bash\nwrangler deploy\n```", True),
        ("Command blocks are syntax examples, not execution orders.\nRun `wrangler deploy` now.", True),
        ("```bash\nwrangler deploy\n```", True),
        ("Ejecuta `wrangler deploy --dry-run`.", False),
        ("Ejecuta `wrangler deploy --dry-run; wrangler deploy`.", True),
        ("## Examples\nEjecuta `wrangler secret put KEY`.", True),
    ],
)
def test_deployment_examples_do_not_hide_execution_orders(tmp_path: Path, text: str, expected: bool) -> None:
    path = tmp_path / "rule.md"
    path.write_text(text)
    assert any(v.rule_id == "SEM-003" for v in scan_markdown_files([path])) == expected


@pytest.mark.parametrize("order", ["You must deploy now:", "Execute the following\nusing the configured environment:"])
def test_wrapped_orders_override_example_context(tmp_path: Path, order: str) -> None:
    path = tmp_path / "rule.md"
    path.write_text(f"## Examples\n{order}\n```bash\nwrangler deploy\n```")
    assert any(v.rule_id == "SEM-003" for v in scan_markdown_files([path]))


def test_path_symlink_confinement_ast_gate(tmp_path: Path) -> None:
    bad = tmp_path / "bad_gate.py"
    bad.write_text("from pathlib import Path\nROOT = Path(__file__).resolve().parents[2]\n", encoding="utf-8")
    violations = scan_python_fail_open([bad])
    assert len(violations) == 1
    assert violations[0].rule_id == "AST-007"

    good = tmp_path / "good_gate.py"
    good.write_text("from pathlib import Path\nROOT = Path(__file__).absolute().parents[2]\n", encoding="utf-8")
    assert scan_python_fail_open([good]) == []


@pytest.mark.parametrize(
    "snippet",
    [
        "import sqlite3\ndef check():\n    try: pass\n    except Exception:\n        return {'ok': True}\n",
        "import sqlite3\ndef check():\n    try: pass\n    except:\n        return {'admitted': True}\n",
    ],
)
def test_sqlite_fail_open_dict_and_broad_except(tmp_path: Path, snippet: str) -> None:
    path = tmp_path / "engine_mod.py"
    path.write_text(snippet, encoding="utf-8")
    violations = scan_python_fail_open([path], check_symlink_resolve=False)
    assert len(violations) == 1
    assert violations[0].rule_id == "AST-006"


def test_audit_scripts_quality_ast_multiline_except_pass() -> None:
    import ast
    from scripts.c5_quality_gates.audit_scripts_quality import find_ast_anti_patterns

    bare_multiline = ast.parse("try:\n    x = 1\nexcept:\n    pass\n")
    findings_bare = find_ast_anti_patterns(bare_multiline, is_quality_gate=False)
    assert len(findings_bare) == 1
    assert findings_bare[0][0] == 3

    broad_gate = ast.parse("try:\n    x = 1\nexcept Exception:\n    pass\n")
    assert len(find_ast_anti_patterns(broad_gate, is_quality_gate=True)) == 1
    assert find_ast_anti_patterns(broad_gate, is_quality_gate=False) == []


def test_git_diff_binary_safe_ast_gate(tmp_path: Path) -> None:
    bad = tmp_path / "bad_diff.py"
    bad.write_text(
        'import subprocess\nsubprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True)\n',
        encoding="utf-8",
    )
    violations = scan_python_fail_open([bad])
    assert len(violations) == 1
    assert violations[0].rule_id == "AST-008"

    good = tmp_path / "good_diff.py"
    good.write_text(
        'import subprocess\nsubprocess.run(["git", "diff", "HEAD"], capture_output=True, text=False)\n',
        encoding="utf-8",
    )
    assert scan_python_fail_open([good]) == []


def test_biometric_gate_legacy_message_ast_gate(tmp_path: Path) -> None:
    bad = tmp_path / "bad_gate.py"
    bad.write_text(
        'import subprocess\nsubprocess.run(["c5_biometric_gate", "--message", "Deploy"])\n',
        encoding="utf-8",
    )
    violations = scan_python_fail_open([bad])
    assert len(violations) == 1
    assert violations[0].rule_id == "AST-009"

    good = tmp_path / "good_gate.py"
    good.write_text(
        'import subprocess\nsubprocess.run(["c5_biometric_gate", "--action", "Deploy", "--causal-hash", "abc"])\n',
        encoding="utf-8",
    )
    assert scan_python_fail_open([good]) == []


def test_struct_cbor_d_specifier_ast_gate(tmp_path: Path) -> None:
    bad = tmp_path / "bad_struct.py"
    bad.write_text("import struct\nstruct.pack('>D', 1.23)\n", encoding="utf-8")
    violations = scan_python_fail_open([bad])
    assert len(violations) == 1
    assert violations[0].rule_id == "AST-010"

    good = tmp_path / "good_struct.py"
    good.write_text("import struct\nstruct.pack('>Bd', 0xFB, 1.23)\n", encoding="utf-8")
    assert scan_python_fail_open([good]) == []


def test_wal_synchronous_full_ast_gate(tmp_path: Path) -> None:
    bad_normal = tmp_path / "bad_normal.py"
    bad_normal.write_text(
        'import sqlite3\nconn = sqlite3.connect(":memory:")\nconn.execute("PRAGMA synchronous = NORMAL;")\n',
        encoding="utf-8",
    )
    violations = scan_python_fail_open([bad_normal])
    assert len(violations) == 1
    assert violations[0].rule_id == "AST-011"

    bad_off = tmp_path / "bad_off.py"
    bad_off.write_text(
        'import sqlite3\nconn = sqlite3.connect(":memory:")\nconn.execute("PRAGMA synchronous=OFF")\n', encoding="utf-8"
    )
    assert any(v.rule_id == "AST-011" for v in scan_python_fail_open([bad_off]))

    bad_numeric = tmp_path / "bad_numeric.py"
    bad_numeric.write_text(
        'import sqlite3\nconn = sqlite3.connect(":memory:")\nconn.execute("PRAGMA synchronous = 1")\n', encoding="utf-8"
    )
    assert any(v.rule_id == "AST-011" for v in scan_python_fail_open([bad_numeric]))

    good_full = tmp_path / "good_full.py"
    good_full.write_text(
        'import sqlite3\nconn = sqlite3.connect(":memory:")\nconn.execute("PRAGMA synchronous = FULL;")\n',
        encoding="utf-8",
    )
    assert scan_python_fail_open([good_full]) == []

    good_query = tmp_path / "good_query.py"
    good_query.write_text(
        'import sqlite3\nconn = sqlite3.connect(":memory:")\nsync = conn.execute("PRAGMA synchronous;").fetchone()[0]\n',
        encoding="utf-8",
    )
    assert scan_python_fail_open([good_query]) == []

    docstring_sample = tmp_path / "docstring_sample.py"
    docstring_sample.write_text(
        '"""Module ensuring PRAGMA synchronous = NORMAL is documented as forbidden."""\n\ndef helper():\n    """Helper notes that PRAGMA synchronous = OFF causes corruption."""\n    return 1\n',
        encoding="utf-8",
    )
    assert scan_python_fail_open([docstring_sample]) == []


def test_canonical_logical_tick_ast_gate(tmp_path: Path) -> None:
    bad_hash_time = tmp_path / "bad_hash_time.py"
    bad_hash_time.write_text(
        'import hashlib, time\nh = hashlib.sha256(f"claim:{time.time()}".encode()).hexdigest()\n',
        encoding="utf-8",
    )
    violations = scan_python_fail_open([bad_hash_time])
    assert len(violations) == 1
    assert violations[0].rule_id == "AST-012"

    bad_fn_time = tmp_path / "bad_fn_time.py"
    bad_fn_time.write_text(
        'import time\ndef compute_canonical_event_hash(payload: str) -> str:\n    return f"{payload}:{time.time()}"\n',
        encoding="utf-8",
    )
    violations_fn = scan_python_fail_open([bad_fn_time])
    assert any(v.rule_id == "AST-012" for v in violations_fn)

    good_logical = tmp_path / "good_logical.py"
    good_logical.write_text(
        'import hashlib\ndef compute_canonical_event_hash(payload: str, logical_tick: int) -> str:\n    return hashlib.sha256(f"{payload}:{logical_tick}".encode()).hexdigest()\n',
        encoding="utf-8",
    )
    assert scan_python_fail_open([good_logical]) == []

    good_wall_clock = tmp_path / "good_wall_clock.py"
    good_wall_clock.write_text(
        "import time\nstart = time.time()\nelapsed = time.time() - start\n",
        encoding="utf-8",
    )
    assert scan_python_fail_open([good_wall_clock]) == []


def test_secure_enclave_point_normalization_ast_gate(tmp_path: Path) -> None:
    bad_raw = tmp_path / "bad_raw.py"
    bad_raw.write_text("sec1_key = b'...' \nder_key = b'...' \nmatch = (sec1_key == der_key)\n", encoding="utf-8")
    violations = scan_python_fail_open([bad_raw])
    assert len(violations) == 1
    assert violations[0].rule_id == "AST-013"

    bad_dict = tmp_path / "bad_dict.py"
    bad_dict.write_text('valid = (response["public_key_sec1"] == policy["spki_der_hex"])\n', encoding="utf-8")
    assert any(v.rule_id == "AST-013" for v in scan_python_fail_open([bad_dict]))

    bad_cryptography_compare = tmp_path / "bad_cryptography_compare.py"
    bad_cryptography_compare.write_text(
        "def bad_compare(pub):\n"
        "    from cryptography.hazmat.primitives import serialization\n"
        "    raw = pub.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)\n"
        "    der = pub.public_bytes(\n"
        "        serialization.Encoding.SubjectPublicKeyInfo,\n"
        "        serialization.PublicFormat.SubjectPublicKeyInfo,\n"
        "    )\n"
        "    return raw == der\n",
        encoding="utf-8",
    )
    assert any(v.rule_id == "AST-013" for v in scan_python_fail_open([bad_cryptography_compare]))

    bad_compressed = tmp_path / "bad_compressed.py"
    bad_compressed.write_text(
        "def bad_compressed_compare(pub):\n"
        "    from cryptography.hazmat.primitives import serialization\n"
        "    comp = pub.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.CompressedPoint)\n"
        "    uncomp = pub.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)\n"
        "    return comp == uncomp\n",
        encoding="utf-8",
    )
    assert any(v.rule_id == "AST-013" for v in scan_python_fail_open([bad_compressed]))

    bad_hash_concat = tmp_path / "bad_hash_concat.py"
    bad_hash_concat.write_text(
        "import hashlib\n"
        "def bad_digest(sec1_bytes: bytes, spki_bytes: bytes) -> bytes:\n"
        "    return hashlib.sha256(sec1_bytes + spki_bytes).digest()\n",
        encoding="utf-8",
    )
    assert any(v.rule_id == "AST-013" for v in scan_python_fail_open([bad_hash_concat]))

    good_cryptography_compare = tmp_path / "good_cryptography_compare.py"
    good_cryptography_compare.write_text(
        "def good_compare(pub, pub_bytes: bytes):\n"
        "    from cryptography.hazmat.primitives import serialization\n"
        "    point_bytes = serialization.load_der_public_key(pub_bytes).public_bytes(\n"
        "        serialization.Encoding.X962,\n"
        "        serialization.PublicFormat.UncompressedPoint,\n"
        "    )\n"
        "    other_point_bytes = pub.other_point\n"
        "    return point_bytes == other_point_bytes\n",
        encoding="utf-8",
    )
    assert scan_python_fail_open([good_cryptography_compare]) == []

    good_func = tmp_path / "good_func.py"
    good_func.write_text("valid = same_public_key(sec1_key, der_key)\n", encoding="utf-8")
    assert scan_python_fail_open([good_func]) == []

    good_norm = tmp_path / "good_norm.py"
    good_norm.write_text("valid = (to_sec1(der_key) == sec1_key)\n", encoding="utf-8")
    assert scan_python_fail_open([good_norm]) == []

    good_sec1_sec1 = tmp_path / "good_sec1_sec1.py"
    good_sec1_sec1.write_text("valid = (sec1_a == sec1_b)\n", encoding="utf-8")
    assert scan_python_fail_open([good_sec1_sec1]) == []


def test_fs_descriptor_nofollow_toctou_ast_gate(tmp_path: Path) -> None:
    bad_is_symlink_open = tmp_path / "bad_is_symlink_open.py"
    bad_is_symlink_open.write_text(
        "def check_file(path):\n"
        "    if path.is_symlink():\n"
        "        raise ValueError('Symlinks forbidden')\n"
        "    with open(path, 'r') as f:\n"
        "        return f.read()\n",
        encoding="utf-8",
    )
    violations = scan_python_fail_open([bad_is_symlink_open])
    assert len(violations) == 1
    assert violations[0].rule_id == "AST-014"

    bad_is_symlink_read_text = tmp_path / "bad_is_symlink_read_text.py"
    bad_is_symlink_read_text.write_text(
        "def check_doc(doc_path):\n    if doc_path.is_symlink():\n        return ''\n    return doc_path.read_text()\n",
        encoding="utf-8",
    )
    violations_text = scan_python_fail_open([bad_is_symlink_read_text])
    assert any(v.rule_id == "AST-014" for v in violations_text)

    bad_os_islink = tmp_path / "bad_os_islink.py"
    bad_os_islink.write_text(
        "import os\n"
        "def scan(target):\n"
        "    if os.path.islink(target):\n"
        "        return None\n"
        "    with open(target, 'rb') as f:\n"
        "        return f.read()\n",
        encoding="utf-8",
    )
    assert any(v.rule_id == "AST-014" for v in scan_python_fail_open([bad_os_islink]))

    bad_path_open = tmp_path / "bad_path_open.py"
    bad_path_open.write_text(
        "def load(target_path):\n"
        "    if not target_path.is_symlink():\n"
        "        with target_path.open('r') as f:\n"
        "            return f.read()\n",
        encoding="utf-8",
    )
    assert any(v.rule_id == "AST-014" for v in scan_python_fail_open([bad_path_open]))

    good_atomic = tmp_path / "good_atomic.py"
    good_atomic.write_text(
        "import os\n"
        "def safe_read(path):\n"
        "    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)\n"
        "    fd = os.open(path, flags)\n"
        "    with os.fdopen(fd, 'r', encoding='utf-8') as f:\n"
        "        return f.read()\n",
        encoding="utf-8",
    )
    assert scan_python_fail_open([good_atomic]) == []

    good_unlink = tmp_path / "good_unlink.py"
    good_unlink.write_text(
        "def remove_symlink(path):\n    if path.is_symlink():\n        path.unlink()\n",
        encoding="utf-8",
    )
    assert scan_python_fail_open([good_unlink]) == []


def test_quality_gates_confinement_helpers_reject_traversal_and_symlinks(tmp_path: Path) -> None:
    from scripts.c5_quality_gates.audit_license_compliance import _is_confined_to_repo as license_confined
    from scripts.c5_quality_gates.audit_ring2_sqlite_isolation import _is_confined_to_repo as ring2_confined
    from scripts.c5_quality_gates.legion_100_agents_full_monorepo import _is_confined_to_repo as legion_confined
    from scripts.c5_quality_gates.swarm_100_stress_campaign import _ensure_confined_to_repo as swarm_confined
    from scripts.c5_quality_gates.symlink_depth_auditor import _is_confined_to_repo as symlink_confined
    from scripts.c5_quality_gates.sync_docs_index import _is_confined_to_repo as docs_confined
    from scripts.c5_quality_gates.sync_version import _ensure_confined_to_repo as version_confined

    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("escape\n", encoding="utf-8")
    inside = repo / "inside.txt"
    inside.write_text("ok\n", encoding="utf-8")
    escape_link = repo / "escape_link.txt"
    escape_link.symlink_to(outside)
    dotdot_path = repo / "sub" / ".." / ".." / "outside.txt"

    for fn in (license_confined, ring2_confined, legion_confined, symlink_confined, docs_confined):
        assert fn(inside, repo) is True
        assert fn(escape_link, repo) is False
        assert fn(dotdot_path, repo) is False

    for ensure_fn in (swarm_confined, version_confined):
        assert ensure_fn(inside, repo) == inside.resolve()
        with pytest.raises(ValueError, match="Unconfined path outside REPO_ROOT"):
            ensure_fn(escape_link, repo)
        with pytest.raises(ValueError, match="Unconfined path outside REPO_ROOT"):
            ensure_fn(dotdot_path, repo)


def test_canonical_hash_float_forbidden_ast_gate(tmp_path: Path) -> None:
    bad_float_arg = tmp_path / "bad_float_arg.py"
    bad_float_arg.write_text(
        "import hashlib\n"
        "def compute_canonical_event_hash(weight: float, logical_tick: int) -> str:\n"
        "    return hashlib.sha256(f'{weight}:{logical_tick}'.encode()).hexdigest()\n",
        encoding="utf-8",
    )
    violations = scan_python_fail_open([bad_float_arg])
    assert any(v.rule_id == "AST-015" for v in violations)

    bad_float_literal = tmp_path / "bad_float_literal.py"
    bad_float_literal.write_text(
        "import hashlib\n"
        "def bft_leaf_hash(logical_tick: int) -> str:\n"
        "    ratio = float(logical_tick) * 0.5\n"
        "    return hashlib.sha256(str(ratio).encode()).hexdigest()\n",
        encoding="utf-8",
    )
    assert any(v.rule_id == "AST-015" for v in scan_python_fail_open([bad_float_literal]))

    good_int_hash = tmp_path / "good_int_hash.py"
    good_int_hash.write_text(
        "import hashlib\n"
        "def compute_canonical_event_hash(weight_bps: int, logical_tick: int) -> str:\n"
        "    return hashlib.sha256(f'{weight_bps}:{logical_tick}'.encode()).hexdigest()\n",
        encoding="utf-8",
    )
    assert scan_python_fail_open([good_int_hash]) == []


def test_fail_closed_audit_except_ast_gate(tmp_path: Path) -> None:
    bad_audit_pass = tmp_path / "bad_audit_pass.py"
    bad_audit_pass.write_text(
        "def audit_contract_state(target):\n"
        "    try:\n"
        "        target.check()\n"
        "    except Exception:\n"
        "        pass\n"
        "    return True\n",
        encoding="utf-8",
    )
    violations = scan_python_fail_open([bad_audit_pass])
    assert len(violations) == 1
    assert violations[0].rule_id == "AST-016"

    good_audit_fail_closed = tmp_path / "good_audit_fail_closed.py"
    good_audit_fail_closed.write_text(
        "def audit_contract_state(target) -> bool:\n"
        "    try:\n"
        "        target.check()\n"
        "    except Exception:\n"
        "        return False\n"
        "    return True\n",
        encoding="utf-8",
    )
    assert scan_python_fail_open([good_audit_fail_closed]) == []
