"""Pruebas del arnés reproducible por terceros (Vector V1).

Cubren: estadística de --repeat, clave Ed25519 efímera, veredicto global,
rechazo de un ledger alterado, plazo del hijo de SIGKILL y CLI.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

GUARDS_PATH = Path(__file__).absolute().parent
SCRIPT = GUARDS_PATH / "c5_third_party_adversarial_suite.py"
if str(GUARDS_PATH) not in sys.path:
    sys.path.insert(0, str(GUARDS_PATH))

import c5_third_party_adversarial_suite as suite  # noqa: E402


def test_summarize_samples_known_values() -> None:
    out = suite.summarize_samples([10.0, 12.0, 14.0])
    assert out["n"] == 3
    assert out["mean"] == 12.0
    assert out["stdev"] == 2.0
    half = 4.303 * 2.0 / (3**0.5)
    assert out["ci95_low"] == pytest.approx(12.0 - half, abs=0.01)
    assert out["ci95_high"] == pytest.approx(12.0 + half, abs=0.01)


def test_summarize_samples_single_value_has_zero_interval() -> None:
    out = suite.summarize_samples([5.0])
    assert out["stdev"] == 0.0
    assert out["ci95_low"] == out["ci95_high"] == 5.0


def test_aggregate_covers_both_engines_and_all_metrics() -> None:
    run = {e: {m: 1.0 for m in suite._BENCH_METRICS} for e in suite._BENCH_ENGINES}
    agg = suite.aggregate_benchmark_runs([run, run, run])
    assert set(agg) == set(suite._BENCH_ENGINES)
    for engine in agg.values():
        assert set(engine) == set(suite._BENCH_METRICS)
        assert all(v["n"] == 3 for v in engine.values())


def test_full_suite_passes_with_repeat_and_ephemeral_keys(tmp_path: Path) -> None:
    report_a = suite.run_full_suite(tmp_path / "a.json", iterations=50, repeat=3)
    report_b = suite.run_full_suite(tmp_path / "b.json", iterations=50, repeat=1)

    assert report_a["overall_verdict"] == "PASS"
    assert report_b["overall_verdict"] == "PASS"

    bench = report_a["pillar_2_quantifiable_head_to_head_benchmark"]
    assert bench["repeat"] == 3
    assert bench["repeat_statistics"]["c5_real_mediated_engine"]["throughput_ops_sec"]["n"] == 3
    assert "repeat_statistics" not in report_b["pillar_2_quantifiable_head_to_head_benchmark"]

    receipt_a = report_a["pillar_3_open_core_cryptographic_verification"]
    receipt_b = report_b["pillar_3_open_core_cryptographic_verification"]
    assert len(receipt_a["public_key_ed25519"]) == 64
    assert receipt_a["public_key_ed25519"] != receipt_b["public_key_ed25519"]
    assert receipt_a["intact_ledger_verification"]["verified"] is True
    assert receipt_a["intact_certificate_verification"]["valid"] is True
    assert receipt_a["tampered_ledger_rejected"] is True
    assert "ENTRY_HASH_MISMATCH" in receipt_a["tampered_rejection_detail"]


def test_adversarial_campaign_all_vectors_pass(tmp_path: Path) -> None:
    results = suite.run_adversarial_os_campaign(tmp_path)
    assert set(results) == {
        "ATK_01_SIGKILL_CRASH_RECOVERY",
        "ATK_02_TOCTOU_SYMLINK_AND_INODE_SWAP",
        "ATK_03_CONCURRENT_TOKEN_REPLAY_16_THREADS",
        "ATK_04_DIRECT_BYPASS_AND_LOCK_SABOTAGE",
    }
    assert [k for k, v in results.items() if not v["passed"]] == []
    assert results["ATK_01_SIGKILL_CRASH_RECOVERY"]["observed_exit_code"] == -9


def test_sigkill_child_worker_fails_if_never_killed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(suite, "_CHILD_SIGKILL_DEADLINE_S", 0.1)
    ready = tmp_path / "ready.flag"
    wal = tmp_path / "wal.db"
    with pytest.raises(TimeoutError, match="SIGKILL not received"):
        suite._child_sigkill_worker(str(wal), str(ready), "ab" * 32)
    assert ready.read_text(encoding="utf-8") == "READY_FOR_SIGKILL\n"
    with contextlib.closing(sqlite3.connect(wal)) as conn:
        assert conn.execute("SELECT nonce, status FROM dispatch_wal").fetchall() == [("ab" * 32, "DISPATCHED_PENDING")]


def test_cli_repeat_flag_emits_json_and_rejects_zero(tmp_path: Path) -> None:
    out = tmp_path / "report.json"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--iterations", "30", "--repeat", "2", "--output", str(out)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["overall_verdict"] == "PASS"
    assert data["pillar_2_quantifiable_head_to_head_benchmark"]["repeat"] == 2

    bad = subprocess.run([sys.executable, str(SCRIPT), "--repeat", "0"], capture_output=True, text=True, timeout=30)
    assert bad.returncode != 0


def test_atk02_report_and_stdout_emit_only_metadata_never_canary_contents(tmp_path: Path) -> None:
    report_path = tmp_path / "atk02_report.json"
    report = suite.run_full_suite(report_path, iterations=20, repeat=1)
    serialized_report = report_path.read_text(encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--iterations", "20", "--repeat", "1"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr

    raw_canary_tokens = (
        suite._ATK02_CANARY_PAYLOAD.decode("utf-8"),
        suite._BENCH_CANARY_PAYLOAD.decode("utf-8"),
    )
    for raw_payload in raw_canary_tokens:
        assert raw_payload not in serialized_report
        assert raw_payload not in proc.stdout

    expected_sha256 = hashlib.sha256(suite._ATK02_CANARY_PAYLOAD).hexdigest()
    for payload_dict in (report, json.loads(proc.stdout)):
        atk02 = payload_dict["pillar_1_adversarial_os_campaigns"]["ATK_02_TOCTOU_SYMLINK_AND_INODE_SWAP"]
        assert atk02["passed"] is True
        assert atk02["symlink_swap_blocked_by_o_nofollow"] is True
        assert atk02["inode_replacement_blocked"] is True
        assert atk02["protected_vault_canary_intact"] is True
        assert atk02["protected_vault_canary_sha256"] == expected_sha256
        assert len(atk02["protected_vault_canary_sha256"]) == 64
        assert all(isinstance(v, bool) or (isinstance(v, str) and len(v) == 64) for v in atk02.values())


def test_atk02_sentinel_digest_verifier_detects_real_tampering(tmp_path: Path) -> None:
    sentinel_path = tmp_path / "protected_vault_sentinel.txt"
    canary_payload = suite._ATK02_CANARY_PAYLOAD
    sentinel_path.write_bytes(canary_payload)
    expected_sha256 = hashlib.sha256(canary_payload).hexdigest()

    assert suite._verify_sentinel_digest(sentinel_path, expected_sha256) is True

    # Mutación real de 1 byte en disco debe fallar la verificación por digest.
    tampered_bytes = canary_payload[:-1] + b"X"
    sentinel_path.write_bytes(tampered_bytes)
    assert suite._verify_sentinel_digest(sentinel_path, expected_sha256) is False

    # Mutación a través de un symlink sin mediación también debe ser detectada.
    sentinel_path.write_bytes(canary_payload)
    assert suite._verify_sentinel_digest(sentinel_path, expected_sha256) is True
    hijack_link = tmp_path / "hijack_link.txt"
    hijack_link.symlink_to(sentinel_path)
    hijack_link.write_bytes(b"OVERWRITTEN_VIA_SYMLINK")
    assert suite._verify_sentinel_digest(sentinel_path, expected_sha256) is False
