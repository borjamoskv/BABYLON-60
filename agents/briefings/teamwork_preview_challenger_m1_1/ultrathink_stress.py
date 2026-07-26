# C5-REAL EXERGY CERTIFIED
# ULTRATHINK LEARNING STRESS HARNESS
import os
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ["CORTEX_BFT_KEY"] = "c5_real_test_key_sovereign_2026"

from scripts.ultrathink_learning import ultrathink_audit

class TestUltrathinkStress(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md")

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_ultrathink_audit_markdown(self):
        self.temp_file.write("# Title\nThis is a test proposal with structural tokens Ω123 C5-REAL AST.")
        self.temp_file.close()

        # Run audit on markdown file
        ultrathink_audit(self.temp_file.name)

    def test_ultrathink_audit_empty(self):
        self.temp_file.write("")
        self.temp_file.close()

        ultrathink_audit(self.temp_file.name)

    def test_ultrathink_audit_python_code(self):
        self.temp_file.write("def foo():\n    return 'C5-REAL'\n")
        self.temp_file.close()

        ultrathink_audit(self.temp_file.name)

if __name__ == "__main__":
    unittest.main()
