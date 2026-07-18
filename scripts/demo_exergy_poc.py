#!/usr/bin/env python3
"""
[C5-REAL] Exergy Optimizer Agent Proof of Concept.
Simulates high-entropy vs. high-exergy code changes and evaluates them using the GELABP framework.
"""
import sys
import os

# Ensure the scripts directory is in path to import exergy agent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exergy_optimizer_agent import evaluate_gelabp

# Define mock diffs representing different development actions
MOCK_DIFF_HIGH_ENTROPY = """
diff --git a/database/connection.py b/database/connection.py
index a123b45..c789d01 100644
--- a/database/connection.py
+++ b/database/connection.py
@@ -10,3 +10,8 @@ def connect():
+    try:
+        db = sqlite3.connect("cortex.db")
+        # Hardcoded master key leak:
+        MASTER_LEDGER_KEY = "3b4dff086c8f9da924ba95f7ecb93ea0"
+    except:
+        # Broad exception catch
+        pass
"""

MOCK_DIFF_HIGH_EXERGY = """
diff --git a/tests/test_c5_invariants.py b/tests/test_c5_invariants.py
index e456f78..b890c12 100644
--- a/tests/test_c5_invariants.py
+++ b/tests/test_c5_invariants.py
@@ -12,3 +12,8 @@
+def test_inv_c5_10_pynacl_serialization():
+    \"\"\"INV_C5_10 — PyNaCl key serialization must not access private attributes like _seed or _public_key.\"\"\"
+    hits = _scan({".py"}, r'\\._seed\\b|\\._public_key\\b')
+    hits = [h for h in hits if "test_c5_invariants.py" not in h]
+    assert not hits, _fail_msg("INV_C5_10 (PyNaCl serialization)", hits)
"""

def print_banner(title: str):
    print("=" * 60)
    print(f"🔹 {title.upper()}")
    print("=" * 60)

def run_poc():
    print_banner("C5-REAL Exergy Agent Proof of Concept")
    
    # Test Scenario 1: Bad code (leak + broad exception + weak pattern)
    print_banner("Scenario 1: Code Mutation containing High Entropy")
    print(f"Mock Diff Content:\n{MOCK_DIFF_HIGH_ENTROPY.strip()}\n")
    exergy, g, e, l, a, b = evaluate_gelabp(MOCK_DIFF_HIGH_ENTROPY)
    print(f"📊 Evaluated Exergy: {exergy:.1f}/1000.0")
    print(f"  G (Gradient):  {g}")
    print(f"  E (Entropy):   {e}")
    print(f"  L (Leverage):  {l}")
    print(f"  A (AutoLoop):  {a}")
    print(f"  B (Bottleneck):{b}")
    print(f"Veredicto: {'🟢 PASS' if exergy >= 700.0 else '🔴 FAIL (Fallo síncrono provocado)'}")
    print()

    # Test Scenario 2: Optimized code (invariant test addition + strict serialization)
    print_banner("Scenario 2: Code Mutation containing High Exergy")
    print(f"Mock Diff Content:\n{MOCK_DIFF_HIGH_EXERGY.strip()}\n")
    exergy2, g2, e2, l2, a2, b2 = evaluate_gelabp(MOCK_DIFF_HIGH_EXERGY)
    print(f"📊 Evaluated Exergy: {exergy2:.1f}/1000.0")
    print(f"  G (Gradient):  {g2}")
    print(f"  E (Entropy):   {e2}")
    print(f"  L (Leverage):  {l2}")
    print(f"  A (AutoLoop):  {a2}")
    print(f"  B (Bottleneck):{b2}")
    print(f"Veredicto: {'🟢 PASS' if exergy2 >= 700.0 else '🔴 FAIL (Fallo síncrono provocado)'}")
    print()

if __name__ == "__main__":
    run_poc()
