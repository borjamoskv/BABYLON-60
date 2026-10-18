"""Security regression for the binary Z3 trace boundary, using the real solver."""

import importlib.util
from pathlib import Path
import struct
import sys
import unittest

SOURCE = Path(__file__).absolute().parents[1] / "01_KISH_ENGINE/babylon60/kernel/ns_z3_firewall.py"
SPEC = importlib.util.spec_from_file_location("security_trace_firewall", SOURCE)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class TraceFramingTests(unittest.TestCase):
    def test_reject_every_partial_record(self):
        firewall = MODULE.NavierStokesZ3Firewall
        valid = struct.pack("<Q", 2)
        self.assertEqual(firewall.eval_trace_bytes(valid), 0)  # warmup / positive control
        for size in range(1, 8):
            with self.subTest(size=size):
                self.assertNotEqual(firewall.eval_trace_bytes(valid + b"\0" * size), 0)


if __name__ == "__main__":
    unittest.main()
