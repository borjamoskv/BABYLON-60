import logging
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exergy_optimizer_agent import evaluate_gelabp
MOCK_DIFF_HIGH_ENTROPY = '\ndiff --git a/database/connection.py b/database/connection.py\nindex a123b45..c789d01 100644\n--- a/database/connection.py\n+++ b/database/connection.py\n@@ -10,3 +10,8 @@ def connect():\n+    try:\n+        db = babylon60.database.core.connect("cortex.db")\n+        # Hardcoded master key leak:\n+        MASTER_LEDGER_KEY = "3b4dff086c8f9da924ba95f7ecb93ea0"\n+    except:\n+        # Broad exception catch\n+        pass\n'
MOCK_DIFF_HIGH_EXERGY = '\ndiff --git a/tests/test_c5_invariants.py b/tests/test_c5_invariants.py\nindex e456f78..b890c12 100644\n--- a/tests/test_c5_invariants.py\n+++ b/tests/test_c5_invariants.py\n@@ -12,3 +12,8 @@\n+def test_inv_c5_10_pynacl_serialization():\n+    """INV_C5_10 — PyNaCl key serialization must not access private attributes like _seed or _public_key."""\n+    hits = _scan({".py"}, r\'\\._seed\\b|\\._public_key\\b\')\n+    hits = [h for h in hits if "test_c5_invariants.py" not in h]\n+    assert not hits, _fail_msg("INV_C5_10 (PyNaCl serialization)", hits)\n'

def print_banner(title: str):
    logging.info('=' * 60)
    logging.info(f'🔹 {title.upper()}')
    logging.info('=' * 60)

def run_poc():
    print_banner('C5-REAL Exergy Agent Proof of Concept')
    print_banner('Scenario 1: Code Mutation containing High Entropy')
    logging.info(f'Mock Diff Content:\n{MOCK_DIFF_HIGH_ENTROPY.strip()}\n')
    exergy, g, e, lev, a, b = evaluate_gelabp(MOCK_DIFF_HIGH_ENTROPY)
    logging.info(f'📊 Evaluated Exergy: {exergy:.1f}/1000.0')
    logging.info(f'  G (Gradient):  {g}')
    logging.info(f'  E (Entropy):   {e}')
    logging.info(f'  L (Leverage):  {lev}')
    logging.info(f'  A (AutoLoop):  {a}')
    logging.info(f'  B (Bottleneck):{b}')
    logging.info(f"Veredicto: {('🟢 PASS' if exergy >= 700.0 else '🔴 FAIL (Fallo síncrono provocado)')}")
    logging.info()
    print_banner('Scenario 2: Code Mutation containing High Exergy')
    logging.info(f'Mock Diff Content:\n{MOCK_DIFF_HIGH_EXERGY.strip()}\n')
    exergy2, g2, e2, l2, a2, b2 = evaluate_gelabp(MOCK_DIFF_HIGH_EXERGY)
    logging.info(f'📊 Evaluated Exergy: {exergy2:.1f}/1000.0')
    logging.info(f'  G (Gradient):  {g2}')
    logging.info(f'  E (Entropy):   {e2}')
    logging.info(f'  L (Leverage):  {l2}')
    logging.info(f'  A (AutoLoop):  {a2}')
    logging.info(f'  B (Bottleneck):{b2}')
    logging.info(f"Veredicto: {('🟢 PASS' if exergy2 >= 700.0 else '🔴 FAIL (Fallo síncrono provocado)')}")
    logging.info()
if __name__ == '__main__':
    run_poc()