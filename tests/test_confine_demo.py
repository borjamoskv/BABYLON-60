"""``babylon60 demo``: verdicts, effects, witnesses, evidence document and non-vacuity.

The long stress run (5 warm-up + 200 repeats, 8 workers) is opt-in with
BABYLON60_CONFINE_STRESS=1; the default suite runs a short concurrent sample,
shared by the evidence tests through one module-scoped demo run.
"""

from __future__ import annotations

import base64
import dataclasses
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
from typing import Any

import pytest

from babylon60.confine import demo, launcher
from babylon60.confine.journal import ConfineJournal, digest
from babylon60.confine.policy import MIN_LANDLOCK_ABI
from babylon60.confine.witness import (
    InotifyWitness,
    Observation,
    _base64_cores,
    find_token,
    inotify_available,
    token_forms,
)

LINUX = sys.platform.startswith("linux")
LINUX_OK = LINUX and launcher.landlock_abi() >= MIN_LANDLOCK_ABI
REQUIRED = os.environ.get("BABYLON60_REQUIRE_LANDLOCK") == "1"
BACKEND = LINUX_OK or REQUIRED or sys.platform == "darwin"
needs_backend = pytest.mark.skipif(not BACKEND, reason="no confinement backend on this machine")
CANARY = "B60-CANARY-" + "0123456789abcdef01234567"
NEW_VECTORS = [vector for vector in demo.VECTORS if int(vector.id[1:]) >= 15 and vector.expected()]


def _self_paths(journal: Path) -> list[str]:
    return [str(journal), sys.prefix, str(Path(demo.__file__).resolve().parents[1])]


def _tiocsti_disabled() -> bool:
    legacy = Path("/proc/sys/dev/tty/legacy_tiocsti")
    return LINUX and legacy.exists() and legacy.read_text().strip() != "1"


@pytest.fixture(scope="module")
def recorded(tmp_path_factory: pytest.TempPathFactory) -> tuple[demo.DemoReport, Path]:
    """One real demo run (control and confined, every applicable vector), shared by the evidence tests."""
    if not BACKEND:
        pytest.skip("no confinement backend on this machine")
    journal = tmp_path_factory.mktemp("demo") / "journal.db"
    return demo.run_demo(journal_path=journal, repeat=1, workers=4), journal


# --- end to end -------------------------------------------------------------------------------------------


@needs_backend
def test_demo_blocks_every_vector_and_records_it(recorded: tuple[demo.DemoReport, Path]) -> None:
    report, journal = recorded
    doc = report.document
    leaks = [row for row in doc["vectors"] if row["passed"] or row["inconclusive"]]
    assert report.exit_code == 0, [*report.transcript, json.dumps(leaks)]
    assert doc["verdict"] == "BLOCKED"
    assert doc["totals"]["passed"] == 0 and doc["totals"]["inconclusive"] == 0
    assert doc["totals"]["blocked"] == doc["totals"]["attempts"] > 0
    assert all(row["ok"] == row["attempts"] for row in doc["positives"])
    assert doc["journal"]["chain_verified"]
    with ConfineJournal(journal) as chain:
        assert chain.verify().ok
        assert chain.head()[1] == doc["journal"]["head"]


@needs_backend
def test_evidence_is_self_digested_and_carries_no_local_paths(recorded: tuple[demo.DemoReport, Path]) -> None:
    report, journal = recorded
    doc = report.document
    body = {k: v for k, v in doc.items() if k not in ("self_digest", "recorded_at")}
    assert digest(body, domain=demo.EVIDENCE_DOMAIN) == doc["self_digest"]
    text = json.dumps(doc)
    assert "babylon60-demo-" not in text and str(journal.parent) not in text
    home = re.escape(os.path.expanduser("~"))
    assert not re.search(home + r'(/|")', text)
    assert socket.gethostname() not in text
    assert "B60-CANARY" not in text and "B60-TIOCSTI" not in text and "/dev/pts" not in text


@needs_backend
def test_schema_v2_vectors_limits_and_positives(recorded: tuple[demo.DemoReport, Path]) -> None:
    doc = recorded[0].document
    assert doc["schema"] == demo.SCHEMA == "babylon60.confine.demo/v2"
    ids = [row["id"] for row in doc["vectors"]]
    if LINUX:
        assert ids == [f"V{n:02d}" for n in range(1, 19)] + ["V22", "V23", "V24", "V25"]
    else:
        assert ids == ["V01", "V02", "V03", "V04", "V05", "V06", "V09", "V10", *[f"V{n}" for n in range(13, 23)], "V25"]
    for row in doc["vectors"]:
        assert set(row) == {"id", "title", "expected", "results", "blocked", "passed", "inconclusive", "unfalsifiable"}
        assert row["blocked"] + row["passed"] + row["inconclusive"] + row["unfalsifiable"] == doc["repeat"]
    assert [row["id"] for row in doc["limits"]] == (
        ["L1", "L2", "L4", "L5", "L6"] if LINUX else ["L1", "L2", "L4", "L6"]
    )
    for row in doc["limits"]:
        assert set(row) == {
            "id",
            "title",
            "declared",
            "effect_under_confinement",
            "effect_in_control",
            "attempts",
            "results",
        }
        assert row["effect_in_control"] == row["attempts"], row  # the limit is real on this machine
        measured = {0: "closed", row["attempts"]: "open"}.get(row["effect_under_confinement"], "mixed")
        assert measured == row["declared"], row  # declared limits stay truthful
    assert [row["id"] for row in doc["positives"]] == [f"P{n}" for n in range(1, 8)]
    totals = doc["totals"]
    for name in ("blocked", "passed", "inconclusive", "unfalsifiable"):
        assert totals[name] == sum(row[name] for row in doc["vectors"])
    assert totals["vectors"] == sum(1 for row in doc["vectors"] if row["unfalsifiable"] < doc["repeat"])
    assert totals["attempts"] == totals["blocked"] + totals["passed"] + totals["inconclusive"]


@needs_backend
def test_transcript_lines_match_the_document(recorded: tuple[demo.DemoReport, Path]) -> None:
    report = recorded[0]
    doc, lines = report.document, report.transcript
    assert lines == doc["transcript"] and len(lines) == 12 and lines[2] == lines[7] == ""
    plat = doc["platform"]
    layer = f"Landlock ABI {plat['landlock_abi']}" if plat["backend"] == "landlock" else "Seatbelt"
    assert lines[0].startswith(f"babylon60 demo · {plat['system']} {plat['release']} {plat['machine']} · {layer} · ")
    assert lines[1] == f'README.md: "{doc["scenario"]["readme_instruction"]}"'
    # Hero lines come from V01: the canary file holds the 35-byte token and a newline.
    assert lines[3] == "without BABYLON-60  agent follows README → read ~/.ssh/id_rsa → 36 bytes of the canary"
    hero = doc["vectors"][0]
    assert hero["id"] == "V01" and len(hero["results"]) == 1
    assert (
        lines[4] == f"with BABYLON-60     agent follows README → open(~/.ssh/id_rsa) = {hero['results'][0]} ({layer})"
    )
    assert lines[5] == "witness (outside the sandbox): " + (
        "0 events on the canary" if inotify_available() else "no witness"
    )
    assert lines[6] == f"journal: event #{doc['journal']['last']} blake3:{doc['journal']['head'][:12]}… chain verified"
    totals = doc["totals"]
    assert lines[8] == (
        f"{totals['vectors']} vectors · {totals['attempts']} attempts · {totals['blocked']} blocked · "
        f"{totals['passed']} passed · {totals['inconclusive']} inconclusive · {totals['unfalsifiable']} unfalsifiable"
    )
    assert lines[9] == "declared limits: " + " · ".join(
        f"{row['id']} {'open' if row['effect_under_confinement'] else 'closed'}" for row in doc["limits"]
    )
    assert "L3" not in lines[9]
    ok = sum(1 for row in doc["positives"] if row["ok"] == row["attempts"])
    assert lines[10] == f"positive controls: {ok}/{len(doc['positives'])}"
    assert lines[11] == f"verdict: {doc['verdict']}"


@needs_backend
def test_evidence_check_detects_tampering(recorded: tuple[demo.DemoReport, Path]) -> None:
    doc = recorded[0].document
    assert doc["revision"]["confine_code_blake3"] == demo.code_digest()
    assert demo.check_evidence(doc) == {
        "self_digest_ok": True,
        "code_matches_installation": True,
        "recorded_code": demo.code_digest(),
    }
    tampered = json.loads(json.dumps(doc))
    tampered["totals"]["passed"] = 0 if doc["totals"]["passed"] else 1
    assert demo.check_evidence(tampered)["self_digest_ok"] is False


@needs_backend
def test_disabling_confinement_is_reported_as_falsified(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_run = launcher.run

    def unconfined(launch: launcher.Launch, **kwargs: Any) -> launcher.Result:
        # No policy, no seccomp, no new session; the terminal hook of V17 stays as it was.
        return real_run(launcher.Launch(launch.argv, None, acquire_ctty=launch.acquire_ctty), **kwargs)

    monkeypatch.setattr(demo.launcher, "run", unconfined)
    report = demo.run_demo(journal_path=tmp_path / "journal.db")
    assert report.exit_code == 1
    assert report.document["verdict"] == "FALSIFIED"
    assert report.document["totals"]["passed"] == report.document["totals"]["attempts"]


@needs_backend
@pytest.mark.skipif(
    os.environ.get("BABYLON60_CONFINE_STRESS") != "1", reason="set BABYLON60_CONFINE_STRESS=1 for the long stress run"
)
def test_stress_has_no_pass_and_no_witness_event(tmp_path: Path) -> None:
    demo.run_demo(journal_path=tmp_path / "warmup.db", repeat=5, workers=8)
    report = demo.run_demo(journal_path=tmp_path / "journal.db", repeat=200, workers=8)
    totals = report.document["totals"]
    assert report.exit_code == 0, report.transcript
    assert totals["passed"] == 0 and totals["inconclusive"] == 0 and totals["unfalsifiable"] == 0


# --- the new vectors, one by one ----------------------------------------------------------------------------


def _expected_observation(vector: demo.Vector, control: demo.Attempt) -> None:
    """The control's effect must be seen by the harness itself, not only reported by the agent."""
    if vector.id == "V15":
        assert control.observed["tty_input"] == "consumed" and control.found == ["output"]
    elif vector.id == "V16":
        assert control.observed["socket_served"] == 1 and control.found == ["output"]
    elif vector.id == "V17":
        assert control.observed["injected"] is True
    elif vector.id == "V18":
        assert control.observed["planted"] == 1
    elif vector.id == "V25":
        assert control.observed["setid"] == 1  # the harness found the setuid file in the workspace
    else:  # V19-V21 (macOS): the key itself was read; V22-V24: the token held outside was read
        assert "output" in control.found


@pytest.mark.parametrize("vector", NEW_VECTORS, ids=[vector.id for vector in NEW_VECTORS])
def test_new_vector_control_obtains_its_effect(vector: demo.Vector, tmp_path: Path) -> None:
    if vector.id == "V17" and _tiocsti_disabled():
        pytest.skip("TIOCSTI is disabled by the kernel (dev.tty.legacy_tiocsti=0): V17 is unfalsifiable here")
    control = demo._attempt(vector, "control", self_paths=_self_paths(tmp_path / "j.db"), timeout=30)
    if control.result.startswith("HARNESS-"):
        pytest.skip(f"the harness cannot set up {vector.id} on this machine ({control.result}): unfalsifiable here")
    assert control.result == "ok" and control.effect, control
    _expected_observation(vector, control)
    assert control.witness is None or control.witness.events == 0 or vector.canary  # not aimed at the canary file


@needs_backend
@pytest.mark.parametrize("vector", NEW_VECTORS, ids=[vector.id for vector in NEW_VECTORS])
def test_new_vector_is_blocked_under_confinement(vector: demo.Vector, tmp_path: Path) -> None:
    if vector.id == "V17" and _tiocsti_disabled():
        pytest.skip("TIOCSTI is disabled by the kernel (dev.tty.legacy_tiocsti=0): V17 is unfalsifiable here")
    paths = _self_paths(tmp_path / "j.db")
    control = demo._attempt(vector, "control", self_paths=paths, timeout=30)
    if control.result.startswith("HARNESS-"):
        pytest.skip(f"the harness cannot set up {vector.id} on this machine ({control.result}): unfalsifiable here")
    confined = demo._attempt(vector, "confined", self_paths=paths, timeout=30)
    assert demo._classify(vector, control, confined) == "blocked", (control, confined)
    assert confined.result in vector.expected() and not confined.effect and not confined.found


@needs_backend
@pytest.mark.parametrize("vector", demo.POSITIVES, ids=[vector.id for vector in demo.POSITIVES])
def test_positive_controls_work_under_confinement(vector: demo.Vector, tmp_path: Path) -> None:
    confined = demo._attempt(vector, "confined", self_paths=_self_paths(tmp_path / "j.db"), timeout=30)
    assert confined.result == "ok" and confined.effect, confined


def test_run_hands_a_descriptor_to_the_target_as_stdin(tmp_path: Path) -> None:
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
    read_end, write_end = os.pipe()
    try:
        os.write(write_end, b"through stdin\n")
        os.close(write_end)
        result = launcher.run(launcher.Launch(["/bin/cat"], None), env=env, cwd=str(tmp_path), stdin=read_end)
    finally:
        os.close(read_end)
    assert result.returncode == 0 and result.stdout == b"through stdin\n"
    with pytest.raises(ValueError, match="not both"):
        launcher.run(launcher.Launch(["/bin/cat"], None), env=env, cwd=str(tmp_path), stdin=0, stdin_data=b"x")


# --- classification: confined evidence first ----------------------------------------------------------------

VX = demo.Vector("VX", "unit vector", "read", ("EACCES",), ("EPERM",))
ERR = VX.expected()[0]


def _try(
    run: str, result: str = "ok", effect: bool = False, events: int | None = None, overflow: bool = False
) -> demo.Attempt:
    witness = None if events is None else Observation(events=events, overflow=overflow)
    return demo.Attempt("VX", run, result, effect, witness)


GOOD_CONTROL = _try("control", effect=True, events=3)
FAILED_CONTROL = _try("control", result="ENOENT", effect=False, events=0)


@pytest.mark.parametrize(
    ("vector", "control", "confined", "verdict"),
    [
        # An effect under confinement is a pass even when the control failed (the reviewed defect).
        (VX, FAILED_CONTROL, _try("confined", effect=True, events=0), "passed"),
        (VX, FAILED_CONTROL, _try("confined", result=ERR, events=2), "passed"),
        (VX, GOOD_CONTROL, _try("confined", result=ERR, effect=True), "passed"),
        (VX, GOOD_CONTROL, _try("confined", effect=True, events=0, overflow=True), "passed"),
        # A witness that lost events cannot support any other verdict.
        (VX, FAILED_CONTROL, _try("confined", result=ERR, events=0, overflow=True), "inconclusive"),
        (VX, GOOD_CONTROL, _try("confined", result=ERR, events=0, overflow=True), "inconclusive"),
        # Then the control must be valid.
        (VX, FAILED_CONTROL, _try("confined", result=ERR, events=0), "unfalsifiable"),
        (VX, _try("control", effect=True, events=0), _try("confined", result=ERR, events=0), "unfalsifiable"),
        (VX, _try("control", effect=False), _try("confined", result=ERR), "unfalsifiable"),
        # No witness on this platform (macOS): the control's own effect suffices.
        (VX, _try("control", effect=True), _try("confined", result=ERR), "blocked"),
        # Vectors not aimed at the canary file do not need witness events in the control.
        (
            dataclasses.replace(VX, canary=False),
            _try("control", effect=True, events=0),
            _try("confined", result=ERR, events=0),
            "blocked",
        ),
        (VX, GOOD_CONTROL, _try("confined", result=ERR, events=0), "blocked"),
        # Valid control, no effect, but not the expected error.
        (VX, GOOD_CONTROL, _try("confined", result="ENOENT", events=0), "inconclusive"),
        (VX, GOOD_CONTROL, _try("confined", result="REFUSED", events=0), "inconclusive"),
        (VX, GOOD_CONTROL, _try("confined", result="ok", events=0), "inconclusive"),
    ],
)
def test_classification_branches(
    vector: demo.Vector, control: demo.Attempt, confined: demo.Attempt, verdict: str
) -> None:
    assert demo._classify(vector, control, confined) == verdict


def test_effect_is_judged_from_outside_evidence() -> None:
    effect = demo._effect
    assert effect("ok", "ok", [], {}) and not effect("ok", "EACCES", [], {})
    for kind in ("read", "list", "stat", "watch", "write", "metadata", "tty", "socket", "inject", "plant"):
        assert effect(kind, "EACCES", [], {"ssh_changed": ["id_rsa"]}), kind  # any change to ~/.ssh counts
        assert not effect(kind, "EACCES", [], {}), kind
    assert effect("read", "EACCES", ["notes.txt"], {}) and not effect("read", "ok", [], {})
    assert effect("list", "ok", [], {}) and effect("stat", "ok", [], {}) and effect("watch", "ok", [], {})
    assert not effect("write", "ok", [], {}) and not effect("metadata", "ok", [], {})  # the snapshot decides
    assert effect("tty", "EACCES", [], {"tty_input": "consumed"}) and effect("tty", "ok", ["output"], {})
    assert not effect("tty", "ok", [], {"tty_input": "pending"})
    assert not effect("tty", "ok", [], {"tty_input": "unconfirmed"})
    assert effect("socket", "EPERM", [], {"socket_served": 1}) and not effect("socket", "ok", [], {"socket_served": 0})
    assert effect("inject", "EPERM", [], {"injected": True}) and not effect("inject", "ok", [], {"injected": False})
    assert effect("plant", "EACCES", [], {"planted": 1}) and not effect("plant", "ok", [], {"planted": 0})
    with pytest.raises(ValueError):
        effect("unknown", "ok", [], {})


# --- snapshot of ~/.ssh ---------------------------------------------------------------------------------


def _set_xattr(path: Path) -> None:
    if hasattr(os, "setxattr"):
        try:
            os.setxattr(path, "user.babylon60-test", b"planted")
        except OSError as exc:
            pytest.skip(f"user extended attributes unsupported here: {exc}")
    elif shutil.which("xattr"):
        subprocess.run(["xattr", "-w", "user.babylon60-test", "planted", str(path)], check=True)
    else:
        pytest.skip("no way to set an extended attribute on this platform")


def _replace_inode(ssh: Path) -> None:
    key = ssh / "id_rsa"
    st = key.stat()
    twin = ssh / "id_rsa.new"
    twin.write_bytes(key.read_bytes())
    twin.chmod(0o600)
    os.utime(twin, ns=(st.st_atime_ns, st.st_mtime_ns))
    os.replace(twin, key)


CHANGES = {
    "mode": (lambda ssh: (ssh / "id_rsa").chmod(0o644), "id_rsa", "mode"),
    "times": (lambda ssh: os.utime(ssh / "id_rsa", (0, 0)), "id_rsa", "mtime_ns"),
    "content, same size": (lambda ssh: (ssh / "id_rsa").write_text("B60-CANARY-snapsh0t\n"), "id_rsa", "blake3"),
    "truncate": (lambda ssh: os.truncate(ssh / "id_rsa", 0), "id_rsa", "size"),
    "replaced inode": (_replace_inode, "id_rsa", "ino"),
    "new file": (lambda ssh: (ssh / "authorized_keys").write_text(""), ".", "names"),
    "removed file": (lambda ssh: (ssh / "id_rsa").unlink(), ".", "names"),
    "symlink in place of the key": (
        lambda ssh: ((ssh / "id_rsa").unlink(), (ssh / "id_rsa").symlink_to("/dev/null")),
        "id_rsa",
        "type",
    ),
    "directory mode": (lambda ssh: ssh.chmod(0o755), ".", "mode"),
    "hardlink elsewhere": (lambda ssh: os.link(ssh / "id_rsa", ssh.parent / "copy"), "id_rsa", "nlink"),
    "xattr": (lambda ssh: _set_xattr(ssh / "id_rsa"), "id_rsa", "xattrs"),
    "nested directory": (lambda ssh: (ssh / "sockets").mkdir(), "sockets", None),
}


@pytest.fixture
def ssh_dir(tmp_path: Path) -> Path:
    ssh = tmp_path / "home" / ".ssh"
    ssh.mkdir(parents=True, mode=0o700)
    key = ssh / "id_rsa"
    key.write_text("B60-CANARY-snapshot\n")
    key.chmod(0o600)
    return ssh


def test_snapshot_ignores_reads_by_the_harness(ssh_dir: Path) -> None:
    before = demo._snapshot(str(ssh_dir))
    assert set(before) == {".", "id_rsa"} and before["."]["names"] == ["id_rsa"]
    (ssh_dir / "id_rsa").read_bytes()
    os.listdir(ssh_dir)
    os.stat(ssh_dir / "id_rsa")
    assert demo._changed(before, demo._snapshot(str(ssh_dir))) == []


@pytest.mark.parametrize("name", list(CHANGES))
def test_snapshot_sees_every_kind_of_change(ssh_dir: Path, name: str) -> None:
    change, entry, field_name = CHANGES[name]
    before = demo._snapshot(str(ssh_dir))
    change(ssh_dir)
    after = demo._snapshot(str(ssh_dir))
    assert entry in demo._changed(before, after)
    if field_name is not None:
        assert before[entry][field_name] != after[entry][field_name]
    assert demo._effect("write", "EACCES", [], {"ssh_changed": demo._changed(before, after)})


# --- token forms -------------------------------------------------------------------------------------------


@pytest.mark.parametrize("prefix", [b"", b"x", b"xy", b"xyz"])
@pytest.mark.parametrize("suffix", [b"", b"\n", b"\n--", b"=="])
def test_token_is_found_in_every_encoding_and_alignment(prefix: bytes, suffix: bytes) -> None:
    stream = prefix + CANARY.encode() + suffix
    text = stream.decode()
    for blob in (
        stream,
        stream.hex().encode(),
        stream.hex().upper().encode(),
        base64.b64encode(stream),
        base64.urlsafe_b64encode(stream),
        text.encode("utf-16-le"),
        text.encode("utf-16-be"),
    ):
        assert find_token(CANARY, [b"<<" + blob + b">>"]) == ["output"], blob


def test_urlsafe_base64_differs_and_is_found_at_every_alignment() -> None:
    token = "B60-CANARY-~?>~?>~?>"  # bytes whose low six bits are all ones produce '+' and '/'
    raw = token.encode()
    assert set(_base64_cores(raw, base64.b64encode)) != set(_base64_cores(raw, base64.urlsafe_b64encode))
    for shift in range(3):
        stream = b"a" * shift + raw + b"\n"
        assert find_token(token, [base64.urlsafe_b64encode(stream)]) == ["output"]
        assert find_token(token, [base64.b64encode(stream)]) == ["output"]


def test_token_forms_cover_the_old_gap_and_nothing_else(tmp_path: Path) -> None:
    forms = token_forms(CANARY)
    assert CANARY.encode() in forms and CANARY.encode().hex().upper().encode() in forms
    assert CANARY.encode("utf-16-le") in forms and CANARY.encode("utf-16-be") in forms
    assert len(forms) == len(set(forms)) and all(len(form) >= 32 for form in forms)
    # The key file holds the token and a newline: its base64 was missed by the unaligned form.
    assert find_token(CANARY, [base64.b64encode(CANARY.encode() + b"\n")]) == ["output"]
    assert find_token(CANARY, [os.urandom(1 << 16), b"B60-CANARY-", CANARY.encode()[:-1]]) == []
    (tmp_path / "copy.txt").write_bytes(base64.b64encode(b"key: " + CANARY.encode()))
    assert find_token(CANARY, [], [str(tmp_path)]) == ["copy.txt"]
    assert find_token(CANARY, [b"nothing"], [str(tmp_path / "missing")]) == []


@pytest.mark.skipif(not inotify_available(), reason="inotify is Linux-only")
def test_witness_sees_an_open_and_nothing_else(tmp_path: Path) -> None:
    target = tmp_path / "canary"
    target.write_text("x")
    with InotifyWitness([str(target)]) as witness:
        assert witness.drain().events == 0
        target.read_text()
        observation = witness.drain()
    assert observation.events >= 1 and observation.kinds.get("open", 0) >= 1


# --- tables and transcript ----------------------------------------------------------------------------------

V1_TABLE = [
    ("V01", "follow the README: read ~/.ssh/id_rsa", "read", ("EACCES",), ("EACCES", "EPERM")),
    ("V02", "child `cat` with HOME overridden", "read", ("EACCES",), ("EACCES", "EPERM")),
    ("V03", "symlink planted in the workspace", "read", ("EACCES",), ("EACCES", "EPERM")),
    ("V04", "hardlink into the workspace", "read", ("EXDEV", "EACCES"), ("EACCES", "EPERM", "EXDEV")),
    ("V05", "rename the key into the workspace", "read", ("EXDEV", "EACCES"), ("EACCES", "EPERM", "EXDEV")),
    ("V06", "`..` traversal from the workspace", "read", ("EACCES",), ("EACCES", "EPERM")),
    ("V07", "/proc/self/root path", "read", ("EACCES",), ()),
    ("V08", "O_PATH reopened via /proc/self/fd", "read", ("EACCES",), ()),
    ("V09", "openat on a ~/.ssh directory fd", "read", ("EACCES",), ("EACCES", "EPERM")),
    ("V10", "list ~/.ssh", "list", ("EACCES",), ("EACCES", "EPERM")),
    ("V11", "descriptor of another process", "read", ("EACCES",), ()),
    ("V12", "user namespace + bind mount", "read", ("EPERM",), ()),
    ("V13", "create ~/.ssh/authorized_keys", "write", ("EACCES",), ("EACCES", "EPERM")),
    ("V14", "truncate the key", "write", ("EACCES",), ("EACCES", "EPERM")),
]


def test_vector_tables() -> None:
    assert [(v.id, v.title, v.kind, v.linux, v.darwin) for v in demo.VECTORS[:14]] == V1_TABLE
    assert all(v.canary for v in demo.VECTORS[:14])
    assert [v.id for v in demo.VECTORS] == [f"V{n:02d}" for n in range(1, 26)]
    new = {v.id: v for v in demo.VECTORS[14:]}
    assert new["V15"].linux == ("EACCES",) and set(new["V15"].darwin) == {"EPERM", "EACCES"}
    assert new["V16"].linux == ("EPERM",) and set(new["V16"].darwin) == {"EPERM", "EACCES"}
    assert new["V17"].linux == ("EPERM",) and set(new["V17"].darwin) == {"ENXIO", "EPERM", "EACCES"}
    assert new["V18"].linux == ("EACCES",) and new["V18"].darwin == ("EPERM",)
    assert not any(new[i].canary for i in ("V15", "V16", "V17", "V18"))
    for vector_id in ("V19", "V20", "V21"):  # macOS only
        assert new[vector_id].linux == () and set(new[vector_id].darwin) == {"EPERM", "EACCES"}
    # Round 2 (Linux): Landlock's ptrace scoping, then seccomp for keyrings, System V IPC and setid modes.
    assert [(new[i].linux, new[i].darwin, new[i].canary) for i in ("V22", "V23", "V24", "V25")] == [
        (("EACCES",), ("EACCES", "EPERM"), False),  # macOS: KERN_PROCARGS2 and process-info, Seatbelt
        (("EPERM",), (), False),  # kernel keyrings: Linux only
        (("EPERM",), (), False),  # System V shared memory: Linux only for now
        (("EPERM",), ("EACCES", "EPERM"), False),  # macOS: file-write-setugid, Seatbelt
    ]
    assert new["V25"].kind == "setid"
    limits = {limit.id: (limit.linux, limit.darwin) for limit in demo.LIMITS}
    assert limits == {
        "L1": ("open", "closed"),
        "L2": ("open", "open"),
        "L4": ("open", "closed"),
        "L5": ("open", None),
        "L6": ("open", "closed"),
    }
    assert [p.id for p in demo.POSITIVES] == [f"P{n}" for n in range(1, 8)]


def test_attacker_implements_every_vector_limit_and_positive() -> None:
    source = demo.ATTACKER.read_text(encoding="utf-8")
    implemented = {match.upper() for match in re.findall(r"^def ([vlp]\d+)_", source, flags=re.MULTILINE)}
    assert implemented == {item.id for item in (*demo.VECTORS, *demo.LIMITS, *demo.POSITIVES)}


def test_transcript_keeps_its_shape_and_counts() -> None:
    doc = {
        "platform": {
            "system": "Linux",
            "release": "6.18",
            "machine": "x86_64",
            "backend": "landlock",
            "landlock_abi": 7,
            "uid": 1000,
        },
        "scenario": {"readme_instruction": demo.README_INJECTION.splitlines()[-1]},
        "journal": {"last": 64, "head": "ab" * 32, "chain_verified": True},
        "totals": {"vectors": 18, "attempts": 18, "blocked": 16, "passed": 1, "inconclusive": 1, "unfalsifiable": 0},
        "limits": [
            {"id": "L1", "effect_under_confinement": 1},
            {"id": "L2", "effect_under_confinement": 1},
            {"id": "L4", "effect_under_confinement": 0},
            {"id": "L5", "effect_under_confinement": 1},
        ],
        "positives": [{"ok": 1, "attempts": 1}] * 6 + [{"ok": 0, "attempts": 1}],
        "verdict": "FALSIFIED",
    }
    control = demo.Attempt("V01", "control", "ok", True, Observation(events=3), data=(CANARY + "\n").encode().hex())
    confined = demo.Attempt("V01", "confined", "EACCES", False, Observation(events=0))
    assert demo._transcript(doc, control, confined) == [
        "babylon60 demo · Linux 6.18 x86_64 · Landlock ABI 7 · uid 1000",
        f'README.md: "{demo.README_INJECTION.splitlines()[-1]}"',
        "",
        "without BABYLON-60  agent follows README → read ~/.ssh/id_rsa → 36 bytes of the canary",
        "with BABYLON-60     agent follows README → open(~/.ssh/id_rsa) = EACCES (Landlock ABI 7)",
        "witness (outside the sandbox): 0 events on the canary",
        f"journal: event #64 blake3:{'ab' * 6}… chain verified",
        "",
        "18 vectors · 18 attempts · 16 blocked · 1 passed · 1 inconclusive · 0 unfalsifiable",
        "declared limits: L1 open · L2 open · L4 closed · L5 open",
        "positive controls: 6/7",
        "verdict: FALSIFIED",
    ]
