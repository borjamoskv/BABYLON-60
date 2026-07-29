# C5-REAL EXERGY CERTIFIED
import json
import sqlite3
from unittest.mock import patch
from scripts.ledger_snapshot_engine import compute_sha256, create_snapshot, main, AUTHOR

def test_author_identity():
    assert "Telmo Dinámico de Moskv" in AUTHOR
    assert "borjamoskv" in AUTHOR

def test_compute_sha256(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("c5-real-ledger-data")
    digest = compute_sha256(f)
    assert isinstance(digest, str)
    assert len(digest) == 64

def test_create_snapshot(tmp_path):
    db_file = tmp_path / "cortex.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE test (id INT)")
    conn.commit()
    conn.close()

    snap_dir = tmp_path / "audit" / "snapshots"
    with patch("scripts.ledger_snapshot_engine.DB_PATH", db_file), \
         patch("scripts.ledger_snapshot_engine.SNAPSHOT_DIR", snap_dir):
        manifest_path = create_snapshot()
        assert manifest_path.exists()
        with open(manifest_path) as mf:
            data = json.load(mf)
            assert data["author"] == AUTHOR
            assert "sha256" in data
            assert (snap_dir / data["snapshot_file"]).exists()

def test_main_success(tmp_path):
    snap_dir = tmp_path / "audit" / "snapshots"
    db_file = tmp_path / "cortex.db"
    sqlite3.connect(db_file).close()

    async def mock_record(manifest_path):
        pass

    with patch("scripts.ledger_snapshot_engine.DB_PATH", db_file), \
         patch("scripts.ledger_snapshot_engine.SNAPSHOT_DIR", snap_dir), \
         patch("scripts.ledger_snapshot_engine.record_snapshot_event", side_effect=mock_record):
        assert main() == 0
