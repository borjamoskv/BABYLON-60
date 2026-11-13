# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
End-to-End Subprocess Integration Test for Moskv Native Host Transducer.
Simulates Chrome Extension Native Messaging IPC communication via standard I/O pipes.
"""

import io
import json
import os
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any, cast


def test_moskv_native_host_e2e_subprocess(tmp_path: Path) -> None:
    repo_root = Path(__file__).parent.parent
    host_script = repo_root / "scripts" / "c5_cli" / "moskv_native_host.py"
    assert host_script.exists(), f"Native host script missing at {host_script}"

    # A queue outside the subprocess state root must remain untouched.
    outside_queue = tmp_path / "operator-home" / ".babylon60" / "native_host_queue" / "prompts.json"
    outside_queue.parent.mkdir(parents=True)
    outside_contents = json.dumps(["Preserve the operator's pending prompt"]).encode()
    outside_queue.write_bytes(outside_contents)
    subprocess_home = tmp_path / "isolated-host-home"
    subprocess_home.mkdir(mode=0o700)
    environment = {**os.environ, "HOME": str(subprocess_home), "USERPROFILE": str(subprocess_home)}
    original_home = os.environ.get("HOME")
    queue_file = subprocess_home / ".babylon60" / "native_host_queue" / "prompts.json"
    assert not queue_file.exists()

    # 1. Enqueue a custom prompt via CLI flag
    enqueue_proc = subprocess.run(
        [sys.executable, str(host_script), "--enqueue", "Acid flamenco 130bpm sub-bass"],
        capture_output=True,
        text=True,
        check=True,
        env=environment,
        timeout=10,
    )
    assert "[✓] Enqueued prompt" in enqueue_proc.stdout

    def encode_frame(payload: dict[str, Any]) -> bytes:
        raw = json.dumps(payload).encode("utf-8")
        return struct.pack("<I", len(raw)) + raw

    messages = [{"cmd": "PING", "payload": "E2E_Probe_001"}, {"status": "READY"}, {"status": "READY"}]
    try:
        # communicate closes stdin after all three frames and enforces one deadline.
        proc = subprocess.run(
            [sys.executable, str(host_script)],
            input=b"".join(encode_frame(message) for message in messages),
            capture_output=True,
            check=True,
            env=environment,
            timeout=10,
        )
        output = io.BytesIO(proc.stdout)

        def read_frame() -> dict[str, Any]:
            header = output.read(4)
            assert len(header) == 4, "Missing response frame header"
            (length,) = struct.unpack("<I", header)
            payload_bytes = output.read(length)
            assert len(payload_bytes) == length, "Incomplete response frame"
            return cast(dict[str, Any], json.loads(payload_bytes.decode("utf-8")))

        pong = read_frame()
        assert pong.get("status") == "PONG"
        assert pong.get("echo") == "E2E_Probe_001"
        assert "timestamp" in pong

        gen_cmd = read_frame()
        assert gen_cmd.get("cmd") == "GENERATE"
        assert gen_cmd.get("prompt") == "Acid flamenco 130bpm sub-bass"

        gen_cmd_default = read_frame()
        assert gen_cmd_default.get("cmd") == "GENERATE"
        assert "heavy bass" in gen_cmd_default.get("prompt", "")

        assert output.read() == b"", "Unexpected trailing native messaging output"
        assert json.loads(queue_file.read_text()) == []

    finally:
        assert outside_queue.read_bytes() == outside_contents
        assert os.environ.get("HOME") == original_home
