"""``babylon60 demo``: verdicts, evidence document, witness and non-vacuity.

The long stress run (5 warm-up + 200 repeats, 8 workers) is opt-in with
BABYLON60_CONFINE_STRESS=1; the default suite runs a short concurrent sample.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import re
import socket
import sys

import pytest

from babylon60.confine import demo, launcher
from babylon60.confine.journal import ConfineJournal, digest
from babylon60.confine.policy import MIN_LANDLOCK_ABI
from babylon60.confine.witness import InotifyWitness, find_token, inotify_available

LINUX_OK = sys.platform.startswith("linux") and launcher.landlock_abi() >= MIN_LANDLOCK_ABI
REQUIRED = os.environ.get("BABYLON60_REQUIRE_LANDLOCK") == "1"
needs_backend = pytest.mark.skipif(
    not (LINUX_OK or REQUIRED or sys.platform == "darwin"), reason="no confinement backend on this machine"
)


@needs_backend
def test_demo_blocks_every_vector_and_records_it(tmp_path: Path) -> None:
    report = demo.run_demo(journal_path=tmp_path / "journal.db", repeat=1, workers=4)
    doc = report.document
    assert report.exit_code == 0, report.transcript
    assert doc["verdict"] == "BLOCKED"
    assert doc["totals"]["passed"] == 0 and doc["totals"]["inconclusive"] == 0
    assert doc["totals"]["blocked"] == doc["totals"]["attempts"] > 0
    assert all(row["ok"] == row["attempts"] for row in doc["positives"])
    assert doc["journal"]["chain_verified"]
    with ConfineJournal(tmp_path / "journal.db") as journal:
        assert journal.verify().ok
        assert journal.head()[1] == doc["journal"]["head"]


@needs_backend
def test_evidence_is_self_digested_and_carries_no_local_paths(tmp_path: Path) -> None:
    doc = demo.run_demo(journal_path=tmp_path / "journal.db").document
    body = {k: v for k, v in doc.items() if k not in ("self_digest", "recorded_at")}
    assert digest(body, domain=demo.EVIDENCE_DOMAIN) == doc["self_digest"]
    text = json.dumps(doc)
    assert "babylon60-demo-" not in text and str(tmp_path) not in text
    home = re.escape(os.path.expanduser("~"))
    assert not re.search(home + r'(/|")', text)
    assert socket.gethostname() not in text
    assert "B60-CANARY" not in text


@needs_backend
def test_disabling_confinement_is_reported_as_falsified(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_run = launcher.run

    def unconfined(launch: launcher.Launch, **kwargs: object) -> launcher.Result:
        return real_run(launcher.Launch(launch.argv, None), **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(demo.launcher, "run", unconfined)
    report = demo.run_demo(journal_path=tmp_path / "journal.db")
    assert report.exit_code == 1
    assert report.document["verdict"] == "FALSIFIED"
    assert report.document["totals"]["passed"] == report.document["totals"]["attempts"]


@pytest.mark.skipif(not inotify_available(), reason="inotify is Linux-only")
def test_witness_sees_an_open_and_nothing_else(tmp_path: Path) -> None:
    target = tmp_path / "canary"
    target.write_text("x")
    with InotifyWitness([str(target)]) as witness:
        assert witness.drain().events == 0
        target.read_text()
        observation = witness.drain()
    assert observation.events >= 1 and observation.kinds.get("open", 0) >= 1


def test_token_is_found_in_raw_hex_and_base64(tmp_path: Path) -> None:
    canary = "B60-CANARY-" + "0" * 16
    assert find_token(canary, [b"..." + canary.encode()]) == ["output"]
    assert find_token(canary, [canary.encode().hex().encode()]) == ["output"]
    assert find_token(canary, [base64.b64encode(canary.encode())]) == ["output"]
    (tmp_path / "copy.txt").write_bytes(canary.encode())
    assert find_token(canary, [], [str(tmp_path)]) == ["copy.txt"]
    assert find_token(canary, [b"nothing"], [str(tmp_path / "missing")]) == []


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


@needs_backend
def test_evidence_check_detects_tampering(tmp_path: Path) -> None:
    doc = demo.run_demo(journal_path=tmp_path / "journal.db").document
    assert doc["revision"]["confine_code_blake3"] == demo.code_digest()
    assert demo.check_evidence(doc) == {
        "self_digest_ok": True,
        "code_matches_installation": True,
        "recorded_code": demo.code_digest(),
    }
    tampered = json.loads(json.dumps(doc))
    tampered["totals"]["passed"] = 0 if doc["totals"]["passed"] else 1
    assert demo.check_evidence(tampered)["self_digest_ok"] is False
