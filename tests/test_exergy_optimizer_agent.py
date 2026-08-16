# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import os
import tempfile

# INV_C5_ENV: exergy_optimizer_agent exige BABYLON_HOME/GEMINI_HOME explícitos en
# import time (Path.home() prohibido). Sandbox aislado fijado ANTES del import;
# sin él, pytest collection crashea con RuntimeError en cualquier runner sin esas envs.
_EXERGY_SANDBOX = tempfile.mkdtemp(prefix="exergy_agent_test_")
os.environ.setdefault("BABYLON_HOME", _EXERGY_SANDBOX)
os.environ.setdefault("GEMINI_HOME", _EXERGY_SANDBOX)

from scripts.c5_thermo.exergy_optimizer_agent import evaluate_gelabp, ExergyFailed, ComplexityVisitor
import ast


def test_complexity_visitor_pass():
    code = """
def simple_func():
    if True:
        for i in range(10):
            print(i)
"""
    tree = ast.parse(code)
    visitor = ComplexityVisitor()
    visitor.visit(tree)
    assert visitor.max_depth == 3


def test_complexity_visitor_fail():
    code = """
def deep_func():
    if True:
        for i in range(10):
            while True:
                try:
                    with open('file.txt') as f:
                        print(f.read())
                except:
                    pass
"""
    tree = ast.parse(code)
    visitor = ComplexityVisitor()
    visitor.visit(tree)
    assert visitor.max_depth == 6


def test_evaluate_gelabp_algebraic_limit(tmp_path):
    code = """
def deep_func():
    if True:
        for i in range(10):
            while True:
                try:
                    with open('file.txt') as f:
                        print(f.read())
                except:
                    pass
"""
    # Create a path that doesn't contain "test_" so evaluate_gelabp doesn't exclude it
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "deep_nesting.py")
        with open(test_file, "w") as f:
            f.write(code)

        diff_text = f"""diff --git a/deep_nesting.py b/{test_file}
index 1234567..890abcd 100644
--- a/deep_nesting.py
+++ b/{test_file}
@@ -0,0 +1,5 @@
+def new_func():
+    pass
"""
        verdict = evaluate_gelabp(diff_text)
        assert isinstance(verdict, ExergyFailed)
        assert any("Algebraic Limit Exceeded" in reason for reason in verdict.reasons)
