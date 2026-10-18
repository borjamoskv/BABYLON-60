# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
End-to-End Subprocess Integration Test for Moskv Native Host Transducer.
Simulates Chrome Extension Native Messaging IPC communication via standard I/O pipes.
"""

import json
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any, cast


def test_moskv_native_host_e2e_subprocess() -> None:
    repo_root = Path(__file__).parent.parent
    host_script = repo_root / "scripts" / "c5_cli" / "moskv_native_host.py"
    assert host_script.exists(), f"Native host script missing at {host_script}"

    # Clear previous queue
    queue_file = Path("/tmp/moskv_fx_queue.json")
    queue_file.unlink(missing_ok=True)

    # 1. Enqueue a custom prompt via CLI flag
    enqueue_proc = subprocess.run(
        [sys.executable, str(host_script), "--enqueue", "Acid flamenco 130bpm sub-bass"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "[✓] Enqueued prompt" in enqueue_proc.stdout

    # 2. Spawn Native Host Transducer as long-running child process
    proc = subprocess.Popen(
        [sys.executable, str(host_script)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Helper: send framed message to child stdin
        def send_frame(payload: dict[str, Any]) -> None:
            raw = json.dumps(payload).encode("utf-8")
            header = struct.pack("<I", len(raw))
            assert proc.stdin is not None
            proc.stdin.write(header + raw)
            proc.stdin.flush()

        # Helper: read framed message from child stdout
        def read_frame(timeout_sec: float = 2.0) -> dict[str, Any]:
            assert proc.stdout is not None
            header = proc.stdout.read(4)
            if len(header) < 4:
                raise EOFError("Child closed pipe before frame header")
            (length,) = struct.unpack("<I", header)
            payload_bytes = proc.stdout.read(length)
            return cast(dict[str, Any], json.loads(payload_bytes.decode("utf-8")))

        # Step 1: Send PING, expect PONG
        send_frame({"cmd": "PING", "payload": "E2E_Probe_001"})
        pong = read_frame()
        assert pong.get("status") == "PONG"
        assert pong.get("echo") == "E2E_Probe_001"
        assert "timestamp" in pong

        # Step 2: Send READY, expect GENERATE with our enqueued prompt
        send_frame({"status": "READY"})
        gen_cmd = read_frame()
        assert gen_cmd.get("cmd") == "GENERATE"
        assert gen_cmd.get("prompt") == "Acid flamenco 130bpm sub-bass"

        # Step 3: Send second READY, queue is now empty, expect fallback default prompt
        send_frame({"status": "READY"})
        gen_cmd_default = read_frame()
        assert gen_cmd_default.get("cmd") == "GENERATE"
        assert "heavy bass" in gen_cmd_default.get("prompt", "")

        # Close stdin cleanly to trigger Turing-Incomplete sentinel EOF halt
        if proc.stdin:
            proc.stdin.close()
        proc.wait(timeout=2.0)
        assert proc.returncode == 0

    finally:
        if proc.poll() is None:
            proc.kill()
        queue_file.unlink(missing_ok=True)
