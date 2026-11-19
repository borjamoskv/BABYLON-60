"""Regression checks for filesystem isolation in the Python test harness."""

import os
from pathlib import Path
import sqlite3
import tempfile

import conftest as harness
import pytest


@pytest.mark.parametrize("interrupted", [False, True])
def test_runtime_isolation_preserves_files_and_restores_process_state(tmp_path: Path, interrupted: bool) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()
    sentinels = [existing / name for name in ("keep.db", "keep.db-wal", "keep.db-shm")]
    for sentinel in sentinels:
        sentinel.write_bytes(b"pre-existing database state")
    case = tmp_path / "case"
    case.mkdir()
    original = (Path.cwd(), os.environ.get("TMPDIR"), tempfile.tempdir)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(harness, "_repo_root", existing)
        fixture = harness.isolate_sqlite_wal_invariants.__wrapped__(case)
        next(fixture)
        try:
            assert Path.cwd() == case / "runtime"
            assert tempfile.gettempdir() == str(case / "runtime")
            assert os.environ["TMPDIR"] == str(case / "runtime")
            with sqlite3.connect("isolated.db") as db:
                db.execute("CREATE TABLE sentinel (value INTEGER)")
        finally:
            if interrupted:
                with pytest.raises(RuntimeError, match="test interrupted"):
                    fixture.throw(RuntimeError("test interrupted"))
            else:
                fixture.close()

    assert (Path.cwd(), os.environ.get("TMPDIR"), tempfile.tempdir) == original
    assert (case / "runtime" / "isolated.db").exists()
    assert all(sentinel.read_bytes() == b"pre-existing database state" for sentinel in sentinels)
