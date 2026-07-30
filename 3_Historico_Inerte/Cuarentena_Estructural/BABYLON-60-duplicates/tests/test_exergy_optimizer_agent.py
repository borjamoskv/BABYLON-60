# C5-REAL EXERGY CERTIFIED
import os
import sys
import importlib.util
from pathlib import Path

_script_path = Path(__file__).resolve().parent.parent / "scripts" / "exergy_optimizer_agent.py"
_spec = importlib.util.spec_from_file_location("exergy_optimizer_agent", _script_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

evaluate_gelabp = _mod.evaluate_gelabp
ExergyFailed = _mod.ExergyFailed
ComplexityVisitor = _mod.ComplexityVisitor
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
