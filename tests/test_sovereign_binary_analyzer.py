# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ TEST SUITE: SOVEREIGN BINARY ANALYZER | STATE: C5-REAL
# ============================================================================
"""
test_sovereign_binary_analyzer.py — Unit and integration tests for SovereignBinaryAnalyzer.
"""

import os
import sys
import unittest
import tempfile

# Ensure src/ is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from babylon60.kernel.sovereign_binary_analyzer import SovereignBinaryAnalyzer, Instruction, BasicBlock


class TestSovereignBinaryAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        # Locate a system executable e.g. /bin/ls or /usr/bin/login
        self.test_binary = "/bin/ls" if os.path.exists("/bin/ls") else "/usr/bin/login"
        self.assertTrue(os.path.exists(self.test_binary), "No suitable system binary found for test.")

    def test_metadata_parsing(self) -> None:
        """Verify binary format and architecture detection."""
        analyzer = SovereignBinaryAnalyzer(self.test_binary)
        meta = analyzer.metadata

        self.assertIn(meta.format, ("Mach-O 64", "Fat Mach-O", "ELF 64", "Raw Binary"))
        self.assertIn(meta.architecture, ("arm64", "x86_64", "multi", "unknown"))
        self.assertEqual(meta.filename, os.path.basename(self.test_binary))

    def test_disassembly_and_cfg_building(self) -> None:
        """Verify section disassembly and Basic Block construction."""
        analyzer = SovereignBinaryAnalyzer(self.test_binary)
        instructions = analyzer.disassemble_section(max_instructions=50)

        # Ensure instructions were parsed
        self.assertIsInstance(instructions, list)
        if instructions:
            self.assertIsInstance(instructions[0], Instruction)
            self.assertGreater(instructions[0].address, 0)

            # Build CFG
            blocks = analyzer.build_cfg(instructions)
            self.assertIsInstance(blocks, dict)
            self.assertGreater(len(blocks), 0)

            first_block_id = list(blocks.keys())[0]
            first_block = blocks[first_block_id]
            self.assertIsInstance(first_block, BasicBlock)

    def test_render_mermaid_html(self) -> None:
        """Verify HTML rendering with Mermaid diagram."""
        analyzer = SovereignBinaryAnalyzer(self.test_binary)
        instructions = analyzer.disassemble_section(max_instructions=30)
        blocks = analyzer.build_cfg(instructions)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = os.path.join(tmp_dir, "cfg_test.html")
            res_file = analyzer.render_mermaid_html(blocks, out_file)

            self.assertTrue(os.path.exists(res_file))
            with open(res_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("BABYLON-60 Sovereign Binary Control Flow Graph", content)
            self.assertIn("mermaid", content)


if __name__ == "__main__":
    unittest.main()
