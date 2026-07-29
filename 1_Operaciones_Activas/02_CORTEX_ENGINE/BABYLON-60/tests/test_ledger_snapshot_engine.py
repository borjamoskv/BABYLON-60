# C5-REAL EXERGY CERTIFIED
import json
import sqlite3
import sys
import importlib.util
import types
from pathlib import Path
from unittest.mock import patch

_script_path = Path(__file__).resolve().parent.parent / "scripts" / "ledger_snapshot_engine.py"
_spec = importlib.util.spec_from_file_location("scripts.ledger_snapshot_engine", _script_path)
_mod = importlib.util.module_from_spec(_spec)

if "scripts" not in sys.modules:
    pkg = types.ModuleType("scripts")
    pkg.__path__ = [str(_script_path.parent)]
    sys.modules["scripts"] = pkg
else:
    if not hasattr(sys.modules["scripts"], "__path__"):
        sys.modules["scripts"].__path__ = [str(_script_path.parent)]

sys.modules["scripts.ledger_snapshot_engine"] = _mod
sys.modules["ledger_snapshot_engine"] = _mod
_spec.loader.exec_module(_mod)

compute_sha256 = _mod.compute_sha256
create_snapshot = _mod.create_snapshot
main = _mod.main
AUTHOR = _mod.AUTHOR

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
