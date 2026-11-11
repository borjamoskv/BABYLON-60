"""Chained confinement journal: integrity, append-only storage and determinism.

Tampering is done the way an attacker with write access would do it: a raw
SQLite connection on the real file, with the append-only triggers dropped. The
CLI tests run ``babylon60 log`` and ``babylon60 run`` through the real argument
parser; the ``run`` ones also need the real confinement backend.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import threading

import pytest

from babylon60.confine.journal import GENESIS, ConfineJournal, JournalError, canonical, digest
from babylon60.confine.launcher import interpreter, landlock_abi
from babylon60.confine.policy import MIN_LANDLOCK_ABI

ROOT = Path(__file__).absolute().parents[1]
BACKEND = (sys.platform.startswith("linux") and landlock_abi() >= MIN_LANDLOCK_ABI) or sys.platform == "darwin"
needs_backend = pytest.mark.skipif(
    not BACKEND and os.environ.get("BABYLON60_REQUIRE_LANDLOCK") != "1", reason="no confinement backend on this machine"
)
# What an agent with write access to the journal would run (the reviewer's proof of concept).
TAMPER = (
    "import sqlite3, sys\n"
    "db = sqlite3.connect(sys.argv[1], isolation_level=None)\n"
    "db.execute('DROP TRIGGER confine_events_no_delete')\n"
    "db.execute('DELETE FROM confine_events')\n"
    "print('TAMPERED', flush=True)\n"
)


def _raw(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), isolation_level=None)
    conn.execute("DROP TRIGGER IF EXISTS confine_events_no_update")
    conn.execute("DROP TRIGGER IF EXISTS confine_events_no_delete")
    return conn


def test_chain_verifies_and_head_matches(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        first = journal.append("session_start", {"policy": "a" * 64})
        second = journal.append("session_end", {"exit_code": 0})
        assert first.prev == GENESIS and second.prev == first.digest
        assert (first.logical_tick, second.logical_tick) == (1, 2)
        assert journal.head() == (second.seq, second.digest)
        result = journal.verify()
        assert result.ok and result.events == 2 and result.head == second.digest


def test_full_sync_and_wal_are_enforced(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        assert journal._conn.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert journal._conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_rows_cannot_be_updated_or_deleted(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        journal.append("session_start", {})
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            journal._conn.execute("UPDATE confine_events SET body='{}'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            journal._conn.execute("DELETE FROM confine_events")


def test_tampered_body_is_located(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    with ConfineJournal(path) as journal:
        for code in range(3):
            journal.append("vector", {"code": code})
    conn = _raw(path)
    conn.execute("UPDATE confine_events SET body=? WHERE seq=2", ('{"code":99}',))
    conn.close()
    with ConfineJournal(path) as journal:
        result = journal.verify()
    assert not result.ok and result.first_invalid_seq == 2
    assert result.reason == "digest does not match body"


def test_deleted_event_breaks_the_link(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    with ConfineJournal(path) as journal:
        for code in range(3):
            journal.append("vector", {"code": code})
    conn = _raw(path)
    conn.execute("DELETE FROM confine_events WHERE seq=2")
    conn.close()
    with ConfineJournal(path) as journal:
        result = journal.verify()
    assert not result.ok and result.first_invalid_seq == 3


def test_wall_clock_metadata_is_outside_the_digest(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    with ConfineJournal(path) as journal:
        entry = journal.append("session_start", {"k": 1})
    expected = digest({"kind": "session_start", "logical_tick": 1, "prev": GENESIS, "body": {"k": 1}})
    assert entry.digest == expected
    conn = _raw(path)
    conn.execute("UPDATE confine_events SET recorded_at='1970-01-01T00:00:00+00:00'")
    conn.close()
    with ConfineJournal(path) as journal:
        assert journal.verify().ok


@pytest.mark.parametrize("value", [{"x": math.nan}, {"x": math.inf}, {1: "a"}, {"x": object()}])
def test_canonical_rejects_ambiguous_values(value: object) -> None:
    with pytest.raises(JournalError):
        canonical(value)


def test_canonical_respects_size_limit() -> None:
    with pytest.raises(JournalError):
        canonical({"x": "a" * 100}, limit=50)


def test_concurrent_appends_stay_contiguous(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    ConfineJournal(path).close()
    errors: list[BaseException] = []

    def writer(name: str) -> None:
        try:
            with ConfineJournal(path) as journal:
                for index in range(25):
                    journal.append("vector", {"writer": name, "index": index})
        except BaseException as exc:  # noqa: BLE001 - surfaced through the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(str(n),)) for n in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors
    with ConfineJournal(path) as journal:
        result = journal.verify()
        ticks = [entry.logical_tick for entry in journal.entries()]
    assert result.ok and result.events == 100
    assert ticks == list(range(1, 101))


def test_entries_limit_returns_the_tail(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        for index in range(5):
            journal.append("vector", {"index": index})
        assert [e.body["index"] for e in journal.entries(limit=2)] == [3, 4]
        assert journal.entries(limit=0) == []


def test_append_many_writes_one_contiguous_chained_batch(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        journal.append("session_start", {})
        batch = journal.append_many([("vector", {"index": index}) for index in range(5)])
        assert [entry.logical_tick for entry in batch] == [2, 3, 4, 5, 6]
        assert all(later.prev == earlier.digest for earlier, later in zip(batch, batch[1:]))
        assert journal.append_many([]) == []
        assert journal.verify().ok and journal.head()[1] == batch[-1].digest


def test_failed_batch_leaves_no_partial_events(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        journal.append("session_start", {})
        with pytest.raises(JournalError):
            journal.append_many([("vector", {"ok": 1}), ("vector", {"bad": math.nan})])
        assert journal.verify().events == 1


def test_body_must_be_a_json_object(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        with pytest.raises(JournalError, match="JSON object"):
            journal.append("vector", [1, 2])  # type: ignore[arg-type]
        assert journal.verify().events == 0


def test_new_directories_are_private_and_existing_ones_are_kept(tmp_path: Path) -> None:
    path = tmp_path / "a" / "b" / "journal.db"
    ConfineJournal(path).close()
    for created in (tmp_path / "a", tmp_path / "a" / "b"):
        assert stat.S_IMODE(created.stat().st_mode) == 0o700, created
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    shared = tmp_path / "shared"
    shared.mkdir()
    shared.chmod(0o755)
    ConfineJournal(shared / "journal.db").close()
    assert stat.S_IMODE(shared.stat().st_mode) == 0o755


def _three_events(path: Path) -> list[str]:
    with ConfineJournal(path) as journal:
        return [journal.append("vector", {"index": index, "name": "é"}).digest for index in range(3)]


def _set(path: Path, sql: str, *params: object) -> None:
    conn = _raw(path)
    conn.execute(sql, params)
    conn.close()


def test_duplicate_keys_in_a_stored_body_are_rejected(tmp_path: Path) -> None:
    """The reviewer's forgery: a first-wins reader sees FALSIFIED, the digest covers BLOCKED."""
    path = tmp_path / "j.db"
    with ConfineJournal(path) as journal:
        start = journal.append("demo_start", {})
        end = journal.append("demo_end", {"results_digest": "ab" * 32, "verdict": "BLOCKED"})
    forged = '{"verdict":"FALSIFIED","results_digest":"' + "ab" * 32 + '","verdict":"BLOCKED"}'
    # Non-vacuity: a last-wins parser rebuilds exactly the digested event.
    assert (
        digest({"kind": "demo_end", "logical_tick": 2, "prev": start.digest, "body": json.loads(forged)}) == end.digest
    )
    _set(path, "UPDATE confine_events SET body=? WHERE seq=2", forged)
    with ConfineJournal(path) as journal:
        result = journal.verify()
    assert not result.ok and not result.chain_intact
    assert (result.first_invalid_seq, result.reason) == (2, "body has duplicate key 'verdict'")
    assert result.events == 2 and result.head == start.digest


@pytest.mark.parametrize(
    "stored",
    [
        '{"name":"é","index":1}',  # reordered keys
        '{"index": 1, "name": "é"}',  # whitespace
        '{"index":1,"name":"é"}\n',  # trailing newline
        '{"index":1,"name":"\\u00e9"}',  # escaped instead of raw UTF-8
        '{"index":1.0e0,"name":"é"}',  # another spelling of the number
    ],
)
def test_non_canonical_stored_text_is_rejected(tmp_path: Path, stored: str) -> None:
    path = tmp_path / "j.db"
    digests = _three_events(path)
    assert json.loads(stored) == {"index": 1, "name": "é"}  # same value as the digested body, other text
    _set(path, "UPDATE confine_events SET body=? WHERE seq=2", stored)
    with ConfineJournal(path) as journal:
        result = journal.verify()
    assert not result.ok and result.first_invalid_seq == 2
    assert result.reason.startswith("body text is not the canonical form")
    assert result.head == digests[0]


@pytest.mark.parametrize(
    ("sql", "reason"),
    [
        ("UPDATE confine_events SET logical_tick='two' WHERE seq=2", "logical_tick is stored as text, not integer"),
        ("UPDATE confine_events SET logical_tick=2.5 WHERE seq=2", "logical_tick is stored as real, not integer"),
        ("UPDATE confine_events SET kind=CAST(kind AS BLOB) WHERE seq=2", "kind is stored as blob, not text"),
        ("UPDATE confine_events SET kind='  ' WHERE seq=2", "kind is empty"),
        ("UPDATE confine_events SET body=CAST(body AS BLOB) WHERE seq=2", "body is stored as blob, not text"),
        ("UPDATE confine_events SET body=CAST(x'7b2261223aff7d' AS TEXT) WHERE seq=2", "body is not valid UTF-8"),
        ("UPDATE confine_events SET body='[1]' WHERE seq=2", "body is not a JSON object"),
        ("UPDATE confine_events SET body='{\"x\":NaN}' WHERE seq=2", "body contains NaN, which is not JSON"),
        ("UPDATE confine_events SET prev=upper(prev) WHERE seq=2", "prev is not 64 lowercase hex digits"),
        ("UPDATE confine_events SET digest=upper(digest) WHERE seq=2", "digest is not 64 lowercase hex digits"),
        ("UPDATE confine_events SET digest=CAST(digest AS BLOB) WHERE seq=2", "digest is stored as blob, not text"),
    ],
)
def test_wrong_column_types_are_rejected(tmp_path: Path, sql: str, reason: str) -> None:
    path = tmp_path / "j.db"
    digests = _three_events(path)
    _set(path, sql)
    with ConfineJournal(path) as journal:
        result = journal.verify()
    assert not result.ok and not result.chain_intact
    assert (result.first_invalid_seq, result.reason) == (2, reason)
    assert result.events == 2 and result.head == digests[0]


def test_a_text_seq_is_reported_by_row_position(tmp_path: Path) -> None:
    """A rebuilt table can hold a non-integer seq, which no event number can name."""
    path = tmp_path / "j.db"
    conn = sqlite3.connect(str(path), isolation_level=None)
    conn.execute(
        "CREATE TABLE confine_events (seq TEXT PRIMARY KEY, logical_tick INTEGER, kind TEXT, body TEXT, "
        "prev TEXT, digest TEXT, recorded_at TEXT)"
    )
    event_digest = digest({"kind": "vector", "logical_tick": 1, "prev": GENESIS, "body": {}})
    conn.execute("INSERT INTO confine_events VALUES ('one', 1, 'vector', '{}', ?, ?, '')", (GENESIS, event_digest))
    conn.close()
    with ConfineJournal(path) as journal:
        result = journal.verify()
    assert not result.ok and result.first_invalid_seq is None
    assert result.reason == "row 1: seq is stored as text, not integer"


def test_expected_head_may_be_followed_by_later_events(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        journal.append("run_start", {})
        published = journal.append("run_end", {"exit_code": 0}).digest
        now = journal.verify(expect_head=published)
        assert now.ok and (now.expected_seq, now.events_after_expected) == (2, 0)
        journal.append_many([("run_start", {}), ("run_end", {"exit_code": 1})])
        later = journal.verify(expect_head=published)
        assert later.ok and later.events == 4 and later.head == journal.head()[1]
        assert (later.expected_head, later.expected_seq, later.events_after_expected) == (published, 2, 2)
        genesis = journal.verify(expect_head=GENESIS)  # every chain starts there
        assert genesis.ok and (genesis.expected_seq, genesis.events_after_expected) == (0, 4)


def test_absent_expected_head_fails_an_intact_chain(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    _three_events(path)
    with ConfineJournal(path) as journal:
        plain = journal.verify()
        result = journal.verify(expect_head="ab" * 32)
    assert plain.ok and plain.expected_head is None and plain.expected_seq is None
    assert not result.ok and result.chain_intact and result.first_invalid_seq is None
    assert result.expected_seq is None and result.events_after_expected is None and result.events == 3
    assert result.reason.startswith("expected head not found")


def test_tail_truncation_is_detected_only_with_a_published_head(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    with ConfineJournal(path) as journal:
        for index in range(5):
            journal.append("vector", {"index": index})
        published = journal.head()[1]
    _set(path, "DELETE FROM confine_events WHERE seq > 3")
    with ConfineJournal(path) as journal:
        plain = journal.verify()
        checked = journal.verify(expect_head=published)
        assert plain.ok and plain.events == 3  # a shorter chain is still a valid chain
        assert not checked.ok and checked.chain_intact and checked.expected_seq is None
        journal.append_many([("vector", {"index": 3}), ("vector", {"index": 99})])  # a rewritten tail
        rewritten = journal.verify(expect_head=published)
    assert not rewritten.ok and rewritten.chain_intact and rewritten.events == 5 and rewritten.expected_seq is None


def test_expected_head_before_a_break_still_fails(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    digests = _three_events(path)
    _set(path, "UPDATE confine_events SET body=? WHERE seq=3", '{"index":7,"name":"é"}')
    with ConfineJournal(path) as journal:
        result = journal.verify(expect_head=digests[1])
    assert not result.ok and not result.chain_intact
    assert (result.first_invalid_seq, result.reason) == (3, "digest does not match body")
    assert (result.expected_seq, result.events_after_expected) == (2, 0)


@pytest.mark.parametrize("head", ["ab" * 31, "AB" * 32, "blake3:" + "ab" * 32, "zz" * 32])
def test_malformed_expected_head_is_refused(tmp_path: Path, head: str) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        with pytest.raises(JournalError, match="64 lowercase hex"):
            journal.verify(expect_head=head)


def test_unreadable_entries_raise_journal_error(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    _three_events(path)
    _set(path, "UPDATE confine_events SET body='{' WHERE seq=2")
    with ConfineJournal(path) as journal:
        with pytest.raises(JournalError, match="Unreadable journal entry"):
            journal.entries()


# ``babylon60 log`` and ``babylon60 run`` through the real argument parser.


@pytest.fixture
def box(tmp_path: Path) -> dict[str, Path]:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "README.md").write_text("project\n")
    shared = tmp_path / "shared"
    shared.mkdir()
    return {"home": home, "ws": ws, "shared": shared, "state": tmp_path / "state"}


def _cli(box: dict[str, Path], *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    environ = {name: value for name, value in os.environ.items() if name != "BABYLON_HOME"}
    environ.update({"HOME": str(box["home"]), "PYTHONPATH": str(ROOT / "01_KISH_ENGINE")}, **(env or {}))
    return subprocess.run(
        [sys.executable, "-m", "babylon60.cli.main_dispatcher", *args],
        env=environ,
        cwd=str(box["ws"]),
        capture_output=True,
        text=True,
        timeout=300,
    )


def _published_journal(path: Path) -> tuple[str, str]:
    """Three events; returns (the head published after the second one, the current head)."""
    with ConfineJournal(path) as journal:
        journal.append("run_start", {"argc": 1})
        published = journal.append("run_end", {"exit_code": 0}).digest
        return published, journal.append("run_start", {"argc": 2}).digest


def test_log_expect_head_reports_present_absent_and_malformed(box: dict[str, Path]) -> None:
    path = box["state"] / "journal.db"
    published, head = _published_journal(path)
    found = _cli(box, "log", "--journal", str(path), "--expect-head", published)
    assert found.returncode == 0, found.stdout + found.stderr
    assert f"chain: 3 events, verified, head blake3:{head}\n" in found.stdout  # in full, ready to publish
    assert f"expected head blake3:{published}: found at #2, followed by 1 event\n" in found.stdout
    assert _cli(box, "log", "--journal", str(path), "--expect-head", f" blake3:{published.upper()} ").returncode == 0
    absent = _cli(box, "log", "--journal", str(path), "--expect-head", "ab" * 32)
    assert absent.returncode == 1 and f"expected head blake3:{'ab' * 32}: NOT FOUND" in absent.stdout
    short = _cli(box, "log", "--journal", str(path), "--expect-head", published[:16])
    assert short.returncode == 2 and "64 hex digits" in short.stderr
    payload = json.loads(_cli(box, "log", "--journal", str(path), "--json", "--expect-head", published).stdout)
    assert payload["verified"] and payload["chain_intact"] and payload["head"] == head
    assert payload["expected_head"] == {"digest": published, "found": True, "seq": 2, "events_after": 1}
    missing = _cli(box, "log", "--journal", str(path), "--json", "--expect-head", "ab" * 32)
    report = json.loads(missing.stdout)
    assert missing.returncode == 1 and not report["verified"] and report["chain_intact"]
    assert report["expected_head"] == {"digest": "ab" * 32, "found": False, "seq": None, "events_after": None}


def test_log_detects_truncation_only_with_expect_head(box: dict[str, Path]) -> None:
    path = box["state"] / "journal.db"
    _published, head = _published_journal(path)
    _set(path, "DELETE FROM confine_events WHERE seq = 3")
    plain = _cli(box, "log", "--journal", str(path))
    assert plain.returncode == 0 and "chain: 2 events, verified" in plain.stdout
    checked = _cli(box, "log", "--journal", str(path), "--expect-head", head)
    assert checked.returncode == 1 and "NOT FOUND, the journal was truncated" in checked.stdout


def test_log_without_a_journal_cannot_find_the_expected_head(box: dict[str, Path]) -> None:
    path = box["state"] / "journal.db"
    result = _cli(box, "log", "--journal", str(path), "--expect-head", "ab" * 32)
    assert result.returncode == 1 and "NOT FOUND, there is no journal" in result.stdout
    report = json.loads(_cli(box, "log", "--journal", str(path), "--json").stdout)
    assert report["verified"] and report["events"] == 0 and report["head"] is None
    assert not path.exists() and not path.parent.exists()


def test_log_reports_tampering_without_a_traceback(box: dict[str, Path]) -> None:
    path = box["state"] / "journal.db"
    _published_journal(path)
    _set(path, "UPDATE confine_events SET body=CAST(x'7b2261223aff7d' AS TEXT) WHERE seq=2")
    text = _cli(box, "log", "--journal", str(path))
    assert text.returncode == 1 and "BROKEN at #2: body is not valid UTF-8" in text.stdout
    assert "Traceback" not in text.stderr
    report = json.loads(_cli(box, "log", "--journal", str(path), "--json").stdout)
    assert not report["verified"] and report["first_invalid_seq"] == 2 and report["entries"] == []
    assert "entries_error" in report
    not_a_database = box["state"] / "notes.db"
    not_a_database.write_text("not a database\n" * 100)
    broken = _cli(box, "log", "--journal", str(not_a_database))
    assert broken.returncode == 1 and "Unusable journal" in broken.stderr and "Traceback" not in broken.stderr


def test_log_reports_a_damaged_file_without_a_traceback(box: dict[str, Path]) -> None:
    path = box["state"] / "journal.db"
    with ConfineJournal(path) as journal:
        journal.append_many([("vector", {"index": index, "pad": "x" * 300}) for index in range(200)])
        page_size = journal._conn.execute("PRAGMA page_size").fetchone()[0]
    data = bytearray(path.read_bytes())
    for offset in range(2 * page_size, len(data), page_size):  # every page after the table's root
        data[offset] = 0xFF  # not a b-tree page type
    path.write_bytes(bytes(data))
    with ConfineJournal(path) as journal:
        with pytest.raises(JournalError, match="Unreadable journal"):
            journal.verify()
    result = _cli(box, "log", "--journal", str(path))
    assert result.returncode == 1 and "Unreadable journal" in result.stderr, result.stderr
    assert "Traceback" not in result.stderr


def test_tamper_script_empties_a_reachable_journal(box: dict[str, Path]) -> None:
    """Control for the confined test below: the attack works when the file is reachable."""
    path = box["state"] / "journal.db"
    _published, head = _published_journal(path)
    done = subprocess.run(
        [interpreter(), "-I", "-S", "-c", TAMPER, str(path)], capture_output=True, text=True, timeout=60
    )
    assert done.returncode == 0 and "TAMPERED" in done.stdout, done.stderr
    with ConfineJournal(path) as journal:
        assert journal.verify().ok and journal.verify().events == 0  # an empty chain is a valid chain
        assert not journal.verify(expect_head=head).ok


@needs_backend
def test_new_journal_inside_a_write_grant_is_refused_on_first_use(box: dict[str, Path]) -> None:
    journal = box["shared"] / "new" / "journal.db"
    assert not journal.parent.exists()
    result = _cli(
        box, "run", "--allow-root", "--journal", str(journal), "--allow-write", str(box["shared"]), "--", "true"
    )
    assert result.returncode == 3 and "own state" in result.stderr, result.stderr
    # The journal was created before the policy check; nothing ran and nothing was recorded.
    assert stat.S_IMODE(journal.parent.stat().st_mode) == 0o700
    with ConfineJournal(journal) as opened:
        assert opened.verify().ok and opened.verify().events == 0


@needs_backend
def test_default_journal_under_a_write_grant_is_refused_on_first_use(box: dict[str, Path]) -> None:
    babylon_home = box["shared"] / "babylon-home"
    result = _cli(
        box,
        "run",
        "--allow-root",
        "--allow-write",
        str(box["shared"]),
        "--",
        "true",
        env={"BABYLON_HOME": str(babylon_home)},
    )
    assert result.returncode == 3 and "own state" in result.stderr, result.stderr
    assert (babylon_home / "confine" / "journal.db").exists()


@needs_backend
def test_journal_inside_the_workspace_is_refused(box: dict[str, Path]) -> None:
    result = _cli(box, "run", "--allow-root", "--journal", str(box["ws"] / ".audit" / "journal.db"), "--", "true")
    assert result.returncode == 3 and "own state" in result.stderr, result.stderr


@needs_backend
def test_symlinked_journal_into_a_write_grant_is_refused(box: dict[str, Path]) -> None:
    link = box["state"] / "journal.db"
    link.parent.mkdir()
    link.symlink_to(box["shared"] / "real.db")
    result = _cli(box, "run", "--allow-root", "--journal", str(link), "--allow-write", str(box["shared"]), "--", "true")
    assert result.returncode == 3 and "own state" in result.stderr, result.stderr


@needs_backend
def test_fresh_journal_outside_every_grant_resists_the_agent_and_verifies(box: dict[str, Path]) -> None:
    # The default location (under the home, which is never granted) and a path that does not exist yet.
    journal = box["home"] / ".babylon60" / "confine" / "journal.db"
    result = _cli(
        box,
        "run",
        "--allow-root",
        "--journal",
        str(journal),
        "--",
        interpreter(),
        "-I",
        "-S",
        "-c",
        TAMPER,
        str(journal),
    )
    assert result.returncode != 0 and "TAMPERED" not in result.stdout, result.stdout + result.stderr
    for created in (journal.parent.parent, journal.parent):
        assert stat.S_IMODE(created.stat().st_mode) == 0o700
    assert stat.S_IMODE(journal.stat().st_mode) == 0o600
    log = _cli(box, "log", "--journal", str(journal), "--json")
    payload = json.loads(log.stdout)
    assert log.returncode == 0 and payload["verified"]
    assert [entry["kind"] for entry in payload["entries"]] == ["run_start", "run_end"]
    assert payload["entries"][-1]["body"]["exit_code"] == result.returncode


@needs_backend
def test_dry_run_does_not_create_the_journal(box: dict[str, Path]) -> None:
    journal = box["shared"] / "dry" / "journal.db"
    result = _cli(box, "run", "--allow-root", "--dry-run", "--journal", str(journal), "--", "true")
    assert result.returncode == 0 and json.loads(result.stdout)["policy_digest"], result.stderr
    assert not journal.parent.exists()
