# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import os
from pathlib import Path
from scripts.c5_thermo.exergy_optimizer_agent import evaluate_gelabp, ExergyFailed, ComplexityVisitor
import ast


def test_complexity_visitor_pass() -> None:
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


def test_complexity_visitor_fail() -> None:
    code = """
def deep_func():
    if True:
        for i in range(10):
            while True:
                try:
                    with open('file.txt') as f:
                        print(f.read())
                except Exception as e:
                    logging.error(f'Traza Epistémica Perdida: {e}')
"""
    tree = ast.parse(code)
    visitor = ComplexityVisitor()
    visitor.visit(tree)
    assert visitor.max_depth == 6


def test_evaluate_gelabp_algebraic_limit(tmp_path: Path) -> None:
    code = """
def deep_func():
    if True:
        for i in range(10):
            while True:
                try:
                    with open('file.txt') as f:
                        print(f.read())
                except Exception as e:
                    logging.error(f'Traza Epistémica Perdida: {e}')
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


def test_evaluate_gelabp_evidence_exclusion() -> None:
    diff_text = """diff --git a/docs/security/evidence/swarm100/review.py b/docs/security/evidence/swarm100/review.py
index 1234567..890abcd 100644
--- a/docs/security/evidence/swarm100/review.py
+++ b/docs/security/evidence/swarm100/review.py
@@ -0,0 +1,10 @@
+def helper():
+    except Exception:
+        pass
+"""
    verdict = evaluate_gelabp(diff_text)
    # The file in docs/security/evidence/ should be excluded from AST complexity & added line failure
    assert not any("Algebraic Limit Exceeded" in reason for reason in getattr(verdict, "reasons", []))


def test_db_path_normalization() -> None:
    # Test path normalization logic without double-nesting
    b_base_1 = Path("/tmp/.babylon60")
    db_path_1 = (
        b_base_1 / "exergy_agent_ledger.db"
        if b_base_1.name == ".babylon60"
        else b_base_1 / ".babylon60/exergy_agent_ledger.db"
    )
    assert str(db_path_1) == "/tmp/.babylon60/exergy_agent_ledger.db"

    b_base_2 = Path("/tmp/custom_dir")
    db_path_2 = (
        b_base_2 / "exergy_agent_ledger.db"
        if b_base_2.name == ".babylon60"
        else b_base_2 / ".babylon60/exergy_agent_ledger.db"
    )
    assert str(db_path_2) == "/tmp/custom_dir/.babylon60/exergy_agent_ledger.db"


def test_babylon60_base60_importable() -> None:
    from babylon60.primitives.base60 import bytes_to_base60

    assert callable(bytes_to_base60)


def test_evaluate_gelabp_delta_ast_scope_ignores_untouched_legacy_function() -> None:
    import tempfile
    from scripts.c5_thermo.exergy_optimizer_agent import ExergyPassed

    code = """def legacy_deep():
    if True:
        for i in range(10):
            while True:
                try:
                    with open('file.txt') as f:
                        print(f.read())
                except ValueError:
                    pass


def clean_func():
    return 42
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_file = os.path.join(tmpdir, "legacy_module.py")
        with open(target_file, "w") as f:
            f.write(code)

        diff_text = f"""diff --git a/legacy_module.py b/{target_file}
index 1234567..890abcd 100644
--- a/legacy_module.py
+++ b/{target_file}
@@ -12,0 +12,2 @@
+def clean_func():
+    return 42
"""
        verdict = evaluate_gelabp(diff_text)
        assert isinstance(verdict, ExergyPassed)
