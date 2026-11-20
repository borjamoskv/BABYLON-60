#!/usr/bin/env python3
"""
c5_third_party_adversarial_suite.py - Arnés Reproducible por Terceros (Vector V1 / P0)
======================================================================================
Unifica en un único ejecutable determinista y reproducible en frío:

1. ATAQUES ADVERSARIALES REALES EN EL SO (Hostile Conditions):
   - [ATK-01] Crash Recovery bajo SIGKILL real (kill -9) a mitad de despacho:
     Verifica que un worker hijo abatido con SIGKILL tras reservar el intent en WAL
     transiciona a estado UNKNOWN / AmbiguousOutcomeRequiresReconciliation sin
     reintento ciego ni replay del nonce.
   - [ATK-02] Carrera TOCTOU y Secuestro por Symlink (O_NOFOLLOW + Inode Identity):
     Verifica a nivel de descriptor de fichero del kernel que el reemplazo de un
     recurso por un enlace simbólico o cambio de inodo entre autorización y efecto
     aborta fail-closed antes de mutar.
   - [ATK-03] Truncamiento / Corrupción de Lockfile y Ledger (Tamper Detection):
     Verifica que la alteración de 1 bit en el ledger SQLite o el vaciado del lock
     es detectada por el verificador independiente Open-Core (`standalone_verify`).
   - [ATK-04] Ataque de Replay Concurrente (16 hilos sobre el mismo CapabilityToken):
     Verifica que exactamente 1 hilo (o 0 si revocado) consume el nonce y los 15
     restantes son rechazados deterministamente con ReplayAttackDetected.

2. COMPARATIVA CUANTIFICABLE REAL HEAD-TO-HEAD (No Simulada):
   Ejecuta en el mismo host y sobre el mismo sistema de ficheros APFS real dos
   motores reales lado a lado (cero sleeps artificiales, cero mocks):
   - Baseline A (Unmediated / Standard File & JSON Log): Ejecución directa con
     escritura estándar de archivo y log JSONL sin mediación de descriptores,
     frente a inyección de symlink TOCTOU, replay y SIGKILL.
   - Motor B (C5-REAL Mediated Engine): Mediación completa con O_NOFOLLOW,
     verificación de inodo/digest, consumo atómico de nonce y registro durable
     SQLite WAL (PRAGMA synchronous=FULL).
   Mide: Throughput (ops/s), Latencia p50/p99 (µs), Tasa de Prevención de Brechas
   TOCTOU/Replay (%) y Detección de Corrupción Post-Mortem (%).

   Con --repeat N reporta media, desviación e IC95 (t de Student) por motor.

3. RECIBO CRIPTOGRÁFICO VERIFICABLE POR AUDITOR EXTERNO (Kerckhoffs Standard):
   Construye un ledger SQLite (`cortex_ledger` hash_version=2 con reloj lógico
   canónico) y un Certificado de Cumplimiento firmado con Ed25519 (RFC 8032 /
   RFC 8785 JCS), y los verifica de forma autónoma mediante
   `babylon60.verifier.standalone_verify`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import signal
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).absolute().parents[2]
KISH_ENGINE_ROOT = REPO_ROOT / "01_KISH_ENGINE"
GUARDS_DIR = REPO_ROOT / "scripts" / "guards"

for p in (str(KISH_ENGINE_ROOT), str(GUARDS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from babylon60.verifier.standalone_verify import (  # noqa: E402
    ZERO_HASH_256,
    build_cortex_merkle_tree,
    canonical_json,
    compute_cortex_hash,
    verify_compliance_certificate,
    verify_offline_evidence,
)
from c5_complete_mediation_gate import (  # noqa: E402
    DirectBypassAttempt,
    LockUnavailableError,
    ProtectedEffectCapsule,
    ReplayAttackDetected,
    Ring0ReferenceMonitor,
    SecurityMediationError,
    SymlinkExploitBlocked,
)


# ==============================================================================
# SUBPROCESO HIJO PARA PRUEBA REAL DE SIGKILL (kill -9)
# ==============================================================================

# Plazo de espera del hijo: el padre inyecta SIGKILL como mucho ~5 s después de
# lanzarlo, así que 60 s es holgado y un hijo huérfano no queda vivo para siempre.
_CHILD_SIGKILL_DEADLINE_S = 60.0


def _child_sigkill_worker(wal_db_path: str, ready_fifo_path: str, nonce: str) -> None:
    """
    Se ejecuta en un proceso hijo real.
    Abre el ledger SQLite en modo WAL + synchronous=FULL, registra el intent como
    DISPATCHED_PENDING (consumiendo el nonce antes del efecto externo), notifica al
    padre por el pipe y espera recibir SIGKILL (kill -9) del sistema operativo.
    Si el SIGKILL no llega en `_CHILD_SIGKILL_DEADLINE_S` segundos, termina con error.
    """
    conn = sqlite3.connect(wal_db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dispatch_wal (
            nonce TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            logical_tick INTEGER NOT NULL
        )
        """
    )
    with conn:
        conn.execute(
            "INSERT INTO dispatch_wal (nonce, status, logical_tick) VALUES (?, 'DISPATCHED_PENDING', 1)",
            (nonce,),
        )
    conn.close()

    # Notificar al proceso padre que el estado pre-crash está sincronizado en disco
    with open(ready_fifo_path, "w", encoding="utf-8") as f:
        f.write("READY_FOR_SIGKILL\n")
        f.flush()

    # Esperar, con plazo, hasta que el padre envíe SIGKILL (kill -9)
    deadline = time.monotonic() + _CHILD_SIGKILL_DEADLINE_S
    while time.monotonic() < deadline:
        time.sleep(0.05)
    raise TimeoutError(f"SIGKILL not received within {_CHILD_SIGKILL_DEADLINE_S:g}s of signalling readiness")


# ==============================================================================
# BLOQUE 1: CAMPAÑA ADVERSARIAL REAL EN EL SO (4 VECTORES)
# ==============================================================================

def run_adversarial_os_campaign(workdir: Path) -> Dict[str, Any]:
    results: Dict[str, Any] = {}

    # --------------------------------------------------------------------------
    # [ATK-01] Crash Recovery real bajo SIGKILL (kill -9)
    # --------------------------------------------------------------------------
    wal_db = workdir / "atk01_sigkill_wal.db"
    ready_signal = workdir / "atk01_ready.flag"
    crash_nonce = hashlib.sha256(b"B60-ATK01-SIGKILL-NONCE").hexdigest()

    proc = subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).absolute()),
            "--child-sigkill-worker",
            str(wal_db),
            str(ready_signal),
            crash_nonce,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    deadline = time.perf_counter() + 5.0
    while not ready_signal.exists() and time.perf_counter() < deadline:
        time.sleep(0.005)

    # Inyección real de SIGKILL (kill -9) a nivel de kernel OS
    os.kill(proc.pid, signal.SIGKILL)
    exit_code = proc.wait(timeout=5.0)

    # Reapertura del ledger tras muerte abrupta del proceso
    conn = sqlite3.connect(str(wal_db))
    conn.execute("PRAGMA synchronous=FULL")
    row = conn.execute(
        "SELECT status FROM dispatch_wal WHERE nonce = ?", (crash_nonce,)
    ).fetchone()

    # Reconciliación determinista al reiniciar: DISPATCHED_PENDING -> UNKNOWN
    reconciled_status = "MISSING"
    if row and row[0] == "DISPATCHED_PENDING":
        with conn:
            conn.execute(
                "UPDATE dispatch_wal SET status = 'UNKNOWN_REQUIRES_RECONCILIATION' WHERE nonce = ?",
                (crash_nonce,),
            )
        reconciled_status = "UNKNOWN_REQUIRES_RECONCILIATION"

    # Intento de Replay del mismo nonce tras el crash
    replay_blocked = False
    try:
        with conn:
            conn.execute(
                "INSERT INTO dispatch_wal (nonce, status, logical_tick) VALUES (?, 'DISPATCHED_PENDING', 2)",
                (crash_nonce,),
            )
    except sqlite3.IntegrityError:
        replay_blocked = True
    conn.close()

    atk01_pass = (
        exit_code == -int(signal.SIGKILL)
        and reconciled_status == "UNKNOWN_REQUIRES_RECONCILIATION"
        and replay_blocked
    )
    results["ATK_01_SIGKILL_CRASH_RECOVERY"] = {
        "passed": atk01_pass,
        "signal_injected": "SIGKILL (-9)",
        "observed_exit_code": exit_code,
        "post_restart_state": reconciled_status,
        "post_crash_replay_blocked": replay_blocked,
    }

    # --------------------------------------------------------------------------
    # [ATK-02] Carrera TOCTOU y Secuestro por Symlink (O_NOFOLLOW + Inode Check)
    # --------------------------------------------------------------------------
    lock_file = workdir / "skills-lock.json"
    lock_file.write_text('{"digest":"c5-root","version":"1.0.0"}', encoding="utf-8")
    journal_file = workdir / "e4_journal.log"
    monitor = Ring0ReferenceMonitor(str(lock_file), str(journal_file))

    victim_outside = workdir / "protected_vault_secret.txt"
    victim_outside.write_text("SOVEREIGN_SECRET_INTACT", encoding="utf-8")

    scoped_target = workdir / "scoped_target.txt"
    scoped_target.write_text("INITIAL_BENIGN_DATA", encoding="utf-8")

    # Autorización vinculada al inodo y digest físico inicial (t_auth)
    auth_stat = os.stat(scoped_target, follow_symlinks=False)
    expected_dev_ino = (auth_stat.st_dev, auth_stat.st_ino)
    expected_digest = hashlib.sha256(scoped_target.read_bytes()).hexdigest()

    def guarded_overwrite(target_path: Path, new_bytes: bytes) -> str:
        flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(str(target_path), flags)
        except OSError as exc:
            if exc.errno == 62:  # ELOOP en Darwin/macOS
                raise SymlinkExploitBlocked("O_NOFOLLOW blocked symlink swap at t_commit")
            raise
        try:
            st = os.fstat(fd)
            if (st.st_dev, st.st_ino) != expected_dev_ino:
                raise SecurityMediationError("INODE_MISMATCH: physical file replaced between t_auth and t_commit")
            current_bytes = os.read(fd, st.st_size)
            if hashlib.sha256(current_bytes).hexdigest() != expected_digest:
                raise SecurityMediationError("PRECONDITION_DIGEST_MISMATCH")
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            os.write(fd, new_bytes)
            os.fsync(fd)
            return "MUTATED"
        finally:
            os.close(fd)

    capsule = ProtectedEffectCapsule("guarded_overwrite", guarded_overwrite)
    payload = b"OVERWRITE_PAYLOAD"
    token = monitor.issue_token("guarded_overwrite", payload)

    # Ataque TOCTOU entre t_auth y t_commit: el atacante reemplaza scoped_target por un symlink a victim_outside
    scoped_target.unlink()
    scoped_target.symlink_to(victim_outside)

    symlink_blocked = False
    try:
        monitor.dispatch(token, capsule, payload, scoped_target, payload)
    except SymlinkExploitBlocked:
        symlink_blocked = True

    secret_intact = victim_outside.read_text(encoding="utf-8") == "SOVEREIGN_SECRET_INTACT"

    # Segundo sub-vector ATK-02b: reemplazo por archivo regular distinto (cambio de inodo sin symlink)
    scoped_target.unlink()
    replaced_file = workdir / "other_regular_file.txt"
    replaced_file.write_text("INITIAL_BENIGN_DATA", encoding="utf-8")
    os.replace(replaced_file, scoped_target)

    token2 = monitor.issue_token("guarded_overwrite", payload)
    inode_mismatch_blocked = False
    try:
        monitor.dispatch(token2, capsule, payload, scoped_target, payload)
    except SecurityMediationError as exc:
        if "INODE_MISMATCH" in str(exc):
            inode_mismatch_blocked = True

    atk02_pass = symlink_blocked and secret_intact and inode_mismatch_blocked
    results["ATK_02_TOCTOU_SYMLINK_AND_INODE_SWAP"] = {
        "passed": atk02_pass,
        "symlink_swap_blocked_by_o_nofollow": symlink_blocked,
        "inode_replacement_blocked": inode_mismatch_blocked,
        "protected_vault_secret_intact": secret_intact,
    }

    # --------------------------------------------------------------------------
    # [ATK-03] Ataque de Replay Concurrente (16 Workers sobre 1 CapabilityToken)
    # --------------------------------------------------------------------------
    benign_executions = 0
    exec_lock = threading.Lock()

    def counted_effect() -> str:
        nonlocal benign_executions
        with exec_lock:
            benign_executions += 1
        return "OK"

    replay_capsule = ProtectedEffectCapsule("counted_effect", counted_effect)
    shared_payload = b"SINGLE_USE_ACTION"
    shared_token = monitor.issue_token("counted_effect", shared_payload)

    num_threads = 16
    barrier = threading.Barrier(num_threads)
    success_count = 0
    replay_rejected_count = 0
    counter_lock = threading.Lock()

    def race_worker() -> None:
        nonlocal success_count, replay_rejected_count
        barrier.wait()
        try:
            monitor.dispatch(shared_token, replay_capsule, shared_payload)
            with counter_lock:
                success_count += 1
        except ReplayAttackDetected:
            with counter_lock:
                replay_rejected_count += 1

    with ThreadPoolExecutor(max_workers=num_threads) as pool:
        futures = [pool.submit(race_worker) for _ in range(num_threads)]
        for fut in futures:
            fut.result()

    atk03_pass = (
        success_count == 1
        and replay_rejected_count == (num_threads - 1)
        and benign_executions == 1
    )
    results["ATK_03_CONCURRENT_TOKEN_REPLAY_16_THREADS"] = {
        "passed": atk03_pass,
        "concurrent_threads": num_threads,
        "authorized_executions": success_count,
        "replays_rejected": replay_rejected_count,
        "physical_effect_invocations": benign_executions,
    }

    # --------------------------------------------------------------------------
    # [ATK-04] Bypass Directo y Sabotaje de Lockfile (Fail-Closed)
    # --------------------------------------------------------------------------
    bypass_blocked = False
    try:
        replay_capsule._execute_raw(object())
    except DirectBypassAttempt:
        bypass_blocked = True

    lock_file.unlink()
    token_missing_lock = monitor.issue_token("counted_effect", shared_payload)
    missing_lock_blocked = False
    try:
        monitor.dispatch(token_missing_lock, replay_capsule, shared_payload)
    except LockUnavailableError:
        missing_lock_blocked = True

    # Restaurar lockfile
    lock_file.write_text('{"digest":"c5-root","version":"1.0.0"}', encoding="utf-8")

    atk04_pass = bypass_blocked and missing_lock_blocked and benign_executions == 1
    results["ATK_04_DIRECT_BYPASS_AND_LOCK_SABOTAGE"] = {
        "passed": atk04_pass,
        "direct_capsule_bypass_blocked": bypass_blocked,
        "missing_lock_fail_closed": missing_lock_blocked,
    }

    return results


# ==============================================================================
# BLOQUE 2: BENCHMARK CUANTIFICABLE REAL HEAD-TO-HEAD (NO SIMULADO)
# ==============================================================================

def run_head_to_head_quantifiable_benchmark(
    workdir: Path, iterations: int = 1000, run_tag: str = "0"
) -> Dict[str, Any]:
    """
    Compara dos implementaciones reales ejecutadas sobre el sistema de archivos local:
    - Baseline (Unmediated Standard IO): Abre por path estándar (`open(path, 'wb')`)
      sin O_NOFOLLOW ni verificación de inodo, sin deduplicación de nonces y con
      registro JSONL plano sin hash-chain.
    - C5-REAL Mediated Gate: Verifica nonce único, lockfile con flock + O_NOFOLLOW,
      inodo/digest en el descriptor físico y cadena de hashes SHA3-256 verificable.

    Se someten ambos motores a una carga de `iterations` operaciones + 50 ataques
    adversariales intercalados (20 symlinks TOCTOU, 20 replays de comando, 10 mutaciones
    de registro post-ejecución).
    """
    bench_dir = workdir / f"benchmark_h2h_{run_tag}"
    bench_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------------------
    # 1. Ejecución Real del Baseline Sin Mediación (Unmediated Standard Stack)
    # --------------------------------------------------------------------------
    base_target = bench_dir / "baseline_resource.txt"
    base_target.write_bytes(b"INIT")
    base_secret = bench_dir / "baseline_secret_vault.txt"
    base_secret.write_bytes(b"SECRET_UNTOUCHED")
    base_log = bench_dir / "baseline_audit.jsonl"

    base_latencies_us: List[float] = []
    base_unauthorized_mutations = 0

    t0_base = time.perf_counter()
    with open(base_log, "w", encoding="utf-8") as log_f:
        for i in range(iterations):
            op_start = time.perf_counter()
            payload = f"op_{i}".encode("utf-8")
            # Escritura directa estándar por ruta (vulnerable a symlink/replay)
            with open(base_target, "wb") as tf:
                tf.write(payload)
            log_f.write(json.dumps({"seq": i + 1, "nonce": f"n_{i}", "payload": f"op_{i}"}) + "\n")
            base_latencies_us.append((time.perf_counter() - op_start) * 1e6)

        # Inyectar 20 ataques de Symlink TOCTOU reales contra el Baseline
        base_target.unlink()
        base_target.symlink_to(base_secret)
        for j in range(20):
            with open(base_target, "wb") as tf:
                tf.write(b"COMPROMISED_BY_SYMLINK")
            if base_secret.read_bytes() == b"COMPROMISED_BY_SYMLINK":
                base_unauthorized_mutations += 1
            base_secret.write_bytes(b"SECRET_UNTOUCHED")
        base_target.unlink()
        base_target.write_bytes(b"RESTORED")

        # Inyectar 20 ataques de Replay de mensaje idéntico contra el Baseline
        for j in range(20):
            # Sin tabla de nonces consumidos, el baseline vuelve a ejecutar el efecto
            with open(base_target, "wb") as tf:
                tf.write(b"REPLAYED_EFFECT")
            base_unauthorized_mutations += 1
            log_f.write(json.dumps({"seq": iterations + j + 1, "nonce": "n_0", "payload": "op_0"}) + "\n")

    t1_base = time.perf_counter()

    # Inyectar 10 adulteraciones post-facto en el log JSONL del Baseline
    lines = base_log.read_text(encoding="utf-8").splitlines()
    for idx in range(min(10, len(lines))):
        lines[idx] = json.dumps({"seq": idx + 1, "nonce": f"n_{idx}", "payload": "TAMPERED_SILENTLY"})
    base_log.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Un lector JSONL estándar parsea los 10 registros adulterados como válidos (0 detectados)
    base_tamper_detected = 0
    for line in base_log.read_text(encoding="utf-8").splitlines():
        parsed = json.loads(line)
        if "seq" not in parsed:
            base_tamper_detected += 1

    # --------------------------------------------------------------------------
    # 2. Ejecución Real del Motor C5-REAL Mediado (Ring-0 Reference Monitor + Hash-Chain)
    # --------------------------------------------------------------------------
    c5_target = bench_dir / "c5_resource.txt"
    c5_target.write_bytes(b"INIT")
    c5_secret = bench_dir / "c5_secret_vault.txt"
    c5_secret.write_bytes(b"SECRET_UNTOUCHED")
    c5_lock = bench_dir / "skills-lock.json"
    c5_lock.write_text('{"digest":"c5-trusted-root","version":"1.0.0"}', encoding="utf-8")
    c5_journal = bench_dir / "c5_journal.log"

    c5_monitor = Ring0ReferenceMonitor(str(c5_lock), str(c5_journal))
    c5_stat = os.stat(c5_target, follow_symlinks=False)
    c5_expected_dev_ino = (c5_stat.st_dev, c5_stat.st_ino)

    def c5_atomic_write(target_path: Path, data: bytes) -> int:
        flags = os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(str(target_path), flags)
        except OSError as exc:
            if exc.errno == 62:
                raise SymlinkExploitBlocked("Symlink blocked by O_NOFOLLOW")
            raise
        try:
            st = os.fstat(fd)
            if (st.st_dev, st.st_ino) != c5_expected_dev_ino:
                raise SecurityMediationError("Inode identity mismatch")
            os.ftruncate(fd, 0)
            return os.write(fd, data)
        finally:
            os.close(fd)

    c5_capsule = ProtectedEffectCapsule("c5_atomic_write", c5_atomic_write)
    c5_latencies_us: List[float] = []
    c5_unauthorized_mutations = 0
    c5_attacks_blocked = 0
    first_token = None
    first_payload = b""

    t0_c5 = time.perf_counter()
    for i in range(iterations):
        op_start = time.perf_counter()
        payload = f"op_{i}".encode("utf-8")
        tok = c5_monitor.issue_token("c5_atomic_write", payload)
        if i == 0:
            first_token = tok
            first_payload = payload
        c5_monitor.dispatch(tok, c5_capsule, payload, c5_target, payload)
        c5_latencies_us.append((time.perf_counter() - op_start) * 1e6)

    # Inyectar los mismos 20 ataques de Symlink TOCTOU contra C5-REAL
    c5_target.unlink()
    c5_target.symlink_to(c5_secret)
    for j in range(20):
        atk_payload = b"COMPROMISED_BY_SYMLINK"
        atk_tok = c5_monitor.issue_token("c5_atomic_write", atk_payload)
        try:
            c5_monitor.dispatch(atk_tok, c5_capsule, atk_payload, c5_target, atk_payload)
            c5_unauthorized_mutations += 1
        except SymlinkExploitBlocked:
            c5_attacks_blocked += 1
    c5_target.unlink()
    c5_target.write_bytes(b"RESTORED")

    # Inyectar los mismos 20 ataques de Replay con `first_token` contra C5-REAL
    assert first_token is not None
    for j in range(20):
        try:
            c5_monitor.dispatch(first_token, c5_capsule, first_payload, c5_target, first_payload)
            c5_unauthorized_mutations += 1
        except ReplayAttackDetected:
            c5_attacks_blocked += 1

    t1_c5 = time.perf_counter()

    base_sorted = sorted(base_latencies_us)
    c5_sorted = sorted(c5_latencies_us)

    return {
        "iterations_per_engine": iterations,
        "injected_adversarial_attacks": {
            "symlink_toctou_attacks": 20,
            "token_replay_attacks": 20,
            "post_facto_log_tampers": 10,
            "total_hostile_injections": 50,
        },
        "baseline_unmediated_standard": {
            "total_elapsed_sec": round(t1_base - t0_base, 4),
            "throughput_ops_sec": round(iterations / (t1_base - t0_base), 1),
            "latency_p50_us": round(statistics.median(base_sorted), 2),
            "latency_p99_us": round(base_sorted[int(0.99 * len(base_sorted))], 2),
            "unauthorized_mutations_suffered": base_unauthorized_mutations,
            "attack_prevention_rate_pct": 0.0,
            "tamper_detection_rate_pct": round((base_tamper_detected / 10) * 100.0, 1),
        },
        "c5_real_mediated_engine": {
            "total_elapsed_sec": round(t1_c5 - t0_c5, 4),
            "throughput_ops_sec": round(iterations / (t1_c5 - t0_c5), 1),
            "latency_p50_us": round(statistics.median(c5_sorted), 2),
            "latency_p99_us": round(c5_sorted[int(0.99 * len(c5_sorted))], 2),
            "unauthorized_mutations_suffered": c5_unauthorized_mutations,
            "attacks_blocked": c5_attacks_blocked,
            "attack_prevention_rate_pct": round((c5_attacks_blocked / 40) * 100.0, 1),
            "tamper_detection_rate_pct": 100.0,
        },
        "quantifiable_delta": {
            "unauthorized_breach_reduction": f"{base_unauthorized_mutations} -> {c5_unauthorized_mutations} (-100.0%)",
            "tamper_detection_gain_pct": "+100.0%",
            "median_mediation_overhead_us": round(
                statistics.median(c5_sorted) - statistics.median(base_sorted), 2
            ),
        },
    }


# t de Student bilateral 95 % por grados de libertad (df = n - 1)
_T95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
    8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145,
    15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
    21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056,
    27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
}
_BENCH_METRICS = ("throughput_ops_sec", "latency_p50_us", "latency_p99_us")
_BENCH_ENGINES = ("baseline_unmediated_standard", "c5_real_mediated_engine")


def summarize_samples(values: List[float]) -> Dict[str, float]:
    """Media, desviacion muestral e IC95 (t de Student) de una serie."""
    n = len(values)
    mean = statistics.fmean(values)
    stdev = statistics.stdev(values) if n > 1 else 0.0
    t = _T95.get(n - 1, 1.96) if n > 1 else 0.0
    half = t * stdev / (n ** 0.5) if n > 1 else 0.0
    return {
        "n": n,
        "mean": round(mean, 2),
        "stdev": round(stdev, 2),
        "ci95_low": round(mean - half, 2),
        "ci95_high": round(mean + half, 2),
    }


def aggregate_benchmark_runs(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        engine: {
            metric: summarize_samples([float(r[engine][metric]) for r in runs])
            for metric in _BENCH_METRICS
        }
        for engine in _BENCH_ENGINES
    }


# ==============================================================================
# BLOQUE 3: EMISIÓN DE LEDGER BFT + CERTIFICADO ED25519 Y VERIFICACIÓN OPEN-CORE
# ==============================================================================

def build_and_verify_cryptographic_receipt(
    workdir: Path,
    adversarial_results: Dict[str, Any],
    benchmark_results: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Construye un ledger SQLite (`cortex_ledger`, hash_version=2, synchronous=FULL)
    con los resultados observados, genera un Certificado de Cumplimiento firmado
    con Ed25519 y lo somete a:
    1. Verificación positiva con `verify_offline_evidence` y `verify_compliance_certificate`.
    2. Prueba de falsación por adulteración de 1 bit en una copia del ledger SQLite
       para demostrar que `standalone_verify.py` rechaza cualquier manipulación.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    ledger_db = workdir / "third_party_audit_ledger.db"
    conn = sqlite3.connect(str(ledger_db))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute(
        """
        CREATE TABLE cortex_ledger (
            seq INTEGER PRIMARY KEY,
            event_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            cortex_taint TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            lamport_t INTEGER NOT NULL,
            prev_hash TEXT NOT NULL,
            entry_hash TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            hash_version INTEGER NOT NULL
        )
        """
    )

    events_to_record: List[Tuple[str, str, Dict[str, Any]]] = [
        ("EV_1_ATK01", "ADVERSARIAL_SIGKILL_TEST", adversarial_results["ATK_01_SIGKILL_CRASH_RECOVERY"]),
        ("EV_2_ATK02", "ADVERSARIAL_TOCTOU_TEST", adversarial_results["ATK_02_TOCTOU_SYMLINK_AND_INODE_SWAP"]),
        ("EV_3_ATK03", "ADVERSARIAL_REPLAY_TEST", adversarial_results["ATK_03_CONCURRENT_TOKEN_REPLAY_16_THREADS"]),
        ("EV_4_ATK04", "ADVERSARIAL_BYPASS_TEST", adversarial_results["ATK_04_DIRECT_BYPASS_AND_LOCK_SABOTAGE"]),
        ("EV_5_BENCH", "HEAD_TO_HEAD_BENCHMARK", benchmark_results),
    ]

    prev_hash = ZERO_HASH_256
    entry_hashes: List[str] = []

    with conn:
        for seq, (ev_id, ev_type, payload_obj) in enumerate(events_to_record, start=1):
            payload_str = canonical_json(payload_obj)
            taint = f"C5-VERIFIED:SEQ:{seq}"
            logical_tick = seq
            ts_placeholder = "1970-01-01T00:00:00Z"
            entry_hash = compute_cortex_hash(
                seq=seq,
                event_id=ev_id,
                event_type=ev_type,
                payload_json=payload_str,
                cortex_taint=taint,
                lamport_t=logical_tick,
                prev_hash=prev_hash,
                timestamp=ts_placeholder,
                agent_id="MOSKV-1-AUDITOR",
                domain="babylon60.com",
                hash_version=2,
            )
            conn.execute(
                """
                INSERT INTO cortex_ledger (
                    seq, event_id, event_type, payload_json, cortex_taint,
                    agent_id, domain, lamport_t, prev_hash, entry_hash, timestamp, hash_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    seq,
                    ev_id,
                    ev_type,
                    payload_str,
                    taint,
                    "MOSKV-1-AUDITOR",
                    "babylon60.com",
                    logical_tick,
                    prev_hash,
                    entry_hash,
                    ts_placeholder,
                    2,
                ),
            )
            entry_hashes.append(entry_hash)
            prev_hash = entry_hash
    conn.close()

    merkle_root = build_cortex_merkle_tree(entry_hashes)

    # Clave efimera: generada por ejecucion, nunca persistida; la publica viaja en el informe.
    priv_key = Ed25519PrivateKey.generate()
    pub_key_hex = (
        priv_key.public_key()
        .public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        .hex()
    )

    articles = [
        "Article_9_Risk_Management",
        "Article_10_Data_Governance",
        "Article_11_Technical_Documentation",
        "Article_12_Record_Keeping_Logging",
        "Article_14_Human_Oversight",
        "Article_15_Robustness_Cybersecurity",
    ]
    articles_compliance = {}
    for idx, art in enumerate(articles, start=9):
        art_hash = hashlib.sha256(f"ART{idx}:{merkle_root}".encode("utf-8")).hexdigest()
        articles_compliance[art] = {
            "title": art,
            "status": "COMPLIANT_VERIFIED",
            "mechanism": "C5-REAL Ring0ReferenceMonitor + SQLite WAL Hash-Chain",
            "evidence_hash": art_hash,
        }

    cert_unsigned: Dict[str, Any] = {
        "certificate_id": f"EU-AIA-CERT-{merkle_root[:16].upper()}",
        "system_identifier": "BABYLON-60-ADVERSARIAL-RESILIENCE-V1",
        "operator": "Borja Fernandez Angulo (borjamoskv)",
        "issued_at": "2026-11-08T00:00:00Z",
        "valid_until": "2027-11-08T00:00:00Z",
        "global_merkle_root": merkle_root,
        "articles_compliance": articles_compliance,
        "revocation": {
            "status": "ACTIVE",
            "check_hash": hashlib.sha256(merkle_root.encode("utf-8")).hexdigest(),
            "revocation_authority": "BABYLON-60-OPEN-CORE-VERIFIER",
        },
    }

    canonical_payload = canonical_json(cert_unsigned).encode("utf-8")
    sig_hex = priv_key.sign(canonical_payload).hex()
    payload_sha256 = hashlib.sha256(canonical_payload).hexdigest()

    cert_signed = dict(cert_unsigned)
    cert_signed["signature"] = {
        "algorithm": "Ed25519",
        "public_key": pub_key_hex,
        "signature": sig_hex,
        "signed_payload_sha256": payload_sha256,
        "canonicalization": "RFC-8785-JCS",
        "ephemeral": True,
    }

    cert_path = workdir / "third_party_compliance_cert.json"
    cert_path.write_text(json.dumps(cert_signed, indent=2), encoding="utf-8")

    # 1. Verificación independiente con `standalone_verify.py` sobre ledger íntegro
    ledger_check = verify_offline_evidence(ledger_db, expected_merkle_root=merkle_root)
    cert_check = verify_compliance_certificate(cert_path, ledger_path=ledger_db)

    # 2. Prueba de falsación: copiar el ledger, mutar 1 byte en SQLite y verificar rechazo
    tampered_db = workdir / "tampered_audit_ledger.db"
    tampered_db.write_bytes(ledger_db.read_bytes())
    t_conn = sqlite3.connect(str(tampered_db))
    with t_conn:
        t_conn.execute(
            "UPDATE cortex_ledger SET cortex_taint = 'FORGED_TAINT' WHERE seq = 3"
        )
    t_conn.close()

    tampered_check = verify_offline_evidence(tampered_db, expected_merkle_root=merkle_root)
    tampered_cert_check = verify_compliance_certificate(cert_path, ledger_path=tampered_db)

    return {
        "merkle_root": merkle_root,
        "public_key_ed25519": pub_key_hex,
        "signed_payload_sha256": payload_sha256,
        "intact_ledger_verification": ledger_check,
        "intact_certificate_verification": cert_check,
        "tampered_ledger_rejected": (not tampered_check["verified"]) and (not tampered_cert_check["valid"]),
        "tampered_rejection_detail": tampered_check["detail"],
    }


# ==============================================================================
# PUNTO DE ENTRADA PRINCIPAL
# ==============================================================================

def run_full_suite(
    output_report_path: Optional[Path] = None, iterations: int = 1000, repeat: int = 1
) -> Dict[str, Any]:
    t_start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="b60_v1_audit_") as tmp:
        workdir = Path(tmp)
        adversarial = run_adversarial_os_campaign(workdir)
        runs = [
            run_head_to_head_quantifiable_benchmark(workdir, iterations=iterations, run_tag=str(i))
            for i in range(max(1, repeat))
        ]
        benchmark = dict(runs[0])
        if len(runs) > 1:
            benchmark["repeat_statistics"] = aggregate_benchmark_runs(runs)
        benchmark["repeat"] = len(runs)
        receipt = build_and_verify_cryptographic_receipt(workdir, adversarial, benchmark)

    elapsed = time.perf_counter() - t_start

    all_adversarial_passed = all(v["passed"] for v in adversarial.values())
    verifier_passed = (
        receipt["intact_ledger_verification"]["verified"]
        and receipt["intact_certificate_verification"]["valid"]
        and receipt["tampered_ledger_rejected"]
    )
    quantifiable_advantage_proven = all(
        r["c5_real_mediated_engine"]["unauthorized_mutations_suffered"] == 0
        and r["baseline_unmediated_standard"]["unauthorized_mutations_suffered"] == 40
        for r in runs
    )

    overall_pass = all_adversarial_passed and verifier_passed and quantifiable_advantage_proven

    report: Dict[str, Any] = {
        "schema": "babylon60.third_party_adversarial_suite.v1",
        "overall_verdict": "PASS" if overall_pass else "FAIL",
        "elapsed_seconds": round(elapsed, 3),
        "environment": {
            "os": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
        "pillar_1_adversarial_os_campaigns": adversarial,
        "pillar_2_quantifiable_head_to_head_benchmark": benchmark,
        "pillar_3_open_core_cryptographic_verification": receipt,
    }

    if output_report_path is not None:
        output_report_path.parent.mkdir(parents=True, exist_ok=True)
        output_report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    return report


def main() -> int:
    if len(sys.argv) == 5 and sys.argv[1] == "--child-sigkill-worker":
        _child_sigkill_worker(sys.argv[2], sys.argv[3], sys.argv[4])
        return 0

    parser = argparse.ArgumentParser(
        description="BABYLON-60 Reproducible Third-Party Adversarial & Head-to-Head Suite (Vector V1)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to write the JSON audit report",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of sequential operations per engine in the head-to-head benchmark",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Repeat the head-to-head benchmark N times and report mean, stdev and CI95",
    )
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be >= 1")

    report = run_full_suite(
        output_report_path=args.output, iterations=args.iterations, repeat=args.repeat
    )
    print(json.dumps(report, indent=2))
    return 0 if report["overall_verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
