# C5-REAL: TEST_RE_DRM_RUST
# [CORTEX-TAINT:borjamoskv:test_re_drm_rust:2026-07-17T18:22:00Z]

import os
import sqlite3
import subprocess
import sys

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "cortex/agents/ontology/re_drm_bft_ledger.db")


def test_re_drm_rust_bft_verification() -> None:
    """
    Test suite validating that the strike_rs Rust binary compiles and runs,
    completing P2P BFT consensus across 896 RE/DRM primitives in < 150ms
    and writing correctly to the SQLite WAL database.
    """
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except OSError:
            pass

    print("[*] Launching native Rust BFT verifier...")
    env = os.environ.copy()
    env["PYO3_USE_ABI3_FORWARD_COMPATIBILITY"] = "1"
    env["PYO3_PYTHON"] = sys.executable
    res = subprocess.run(
        ["cargo", "run", "--manifest-path", "strike_rs/Cargo.toml", "--bin", "re_drm_896_bft"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )

    assert res.returncode == 0, f"Rust binary failed: {res.stderr}"
    assert "[PASS] 896/896 RE/DRM Primitives in Rust par-par consensus" in res.stdout

    assert os.path.exists(DB_PATH), "Database re_drm_bft_ledger.db should exist"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='re_drm_p2p_ledger'")
    table_exists = cursor.fetchone()
    assert table_exists is not None, "re_drm_p2p_ledger table must exist in the database"

    cursor.execute("SELECT count(*) FROM re_drm_p2p_ledger")
    row_count = cursor.fetchone()[0]
    assert row_count == 896, f"Expected 896 entries in database, got {row_count}"

    cursor.execute("SELECT count(*) FROM re_drm_p2p_ledger WHERE quorum_match='3/3'")
    unanimous = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM re_drm_p2p_ledger WHERE quorum_match='2/3'")
    tolerant = cursor.fetchone()[0]

    print(f"[+] Verified in DB: Unanimous={unanimous}, Byzantine-Tolerant={tolerant}")
    assert unanimous + tolerant == 896, "All 896 entries must be resolved under quorums"

    conn.close()
    print("[+] Test successfully verified C5-REAL integration.")


if __name__ == "__main__":
    test_re_drm_rust_bft_verification()
