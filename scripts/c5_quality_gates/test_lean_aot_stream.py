#!/usr/bin/env python3
"""Exercise the real Lean AOT binary against framing and transition boundaries."""

from pathlib import Path
import struct
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).absolute().parents[2]
ORACLE = ROOT / "proof/lean/.lake/build/bin/babylon_aot_oracle"


def event(seq: int, thread_id: int, action: int) -> bytes:
    return struct.pack("<Q", (seq << 32) | (thread_id << 8) | action)


class NativeLeanStreamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not ORACLE.is_file():
            raise RuntimeError("Build proof/lean with lake build babylon_aot_oracle before running this gate.")

    def run_trace(self, payload: bytes) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="b60-lean-stream-") as directory:
            trace = Path(directory) / "trace.bin"
            trace.write_bytes(payload)
            return subprocess.run([str(ORACLE), str(trace)], capture_output=True, text=True, timeout=10, check=False)

    def test_valid_empty_and_chunk_boundaries(self) -> None:
        # Warm up the native runtime before the repeated boundary/stress cases.
        self.assertEqual(self.run_trace(event(0, 1, 2)).returncode, 0)
        for count in (0, 1, 1023, 1024, 1025, 4096, 20_000):
            with self.subTest(records=count):
                result = self.run_trace(event(0, 1, 2) * count)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(f"{count} transacciones", result.stdout)

    def test_every_truncated_tail_is_rejected(self) -> None:
        for count in (0, 1, 1023, 1024, 1025):
            for size in range(1, 8):
                with self.subTest(records=count, tail=size):
                    result = self.run_trace(event(0, 1, 2) * count + b"\xff" * size)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn(f"byte {count * 8}", result.stdout)

    def test_invalid_complete_opcode_is_rejected(self) -> None:
        for count in (0, 1023, 1024):
            with self.subTest(records=count):
                result = self.run_trace(event(0, 1, 2) * count + event(0, 1, 255))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_state_survives_chunk_boundary(self) -> None:
        prefix = event(0, 1, 2) * 1023 + event(1, 7, 0)
        accepted = self.run_trace(prefix + event(2, 7, 1) + event(2, 8, 2))
        self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
        for suffix in (event(2, 8, 1), event(1, 8, 2), event(4, 7, 1)):
            with self.subTest(suffix=suffix.hex()):
                rejected = self.run_trace(prefix + suffix)
                self.assertEqual(rejected.returncode, 2, rejected.stdout + rejected.stderr)


if __name__ == "__main__":
    unittest.main()
