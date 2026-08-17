import logging
import os
import sys

logging.basicConfig(level=logging.INFO)
sys.path.insert(0, os.path.abspath('.'))

try:
    import babylon60
    print(f"SUCCESS: Direct babylon60 import -> {babylon60.kernel_status()}")
    if hasattr(babylon60, "safe_kernel_eval"):
        res = babylon60.safe_kernel_eval("NORMAL_PAYLOAD")
        print(f"SUCCESS: safe_kernel_eval -> {res}")
        try:
            babylon60.safe_kernel_eval("TRIGGER_PANIC")
            print("ERROR: Panic was not shielded!")
        except RuntimeError as e:
            print(f"SUCCESS: Panic shield caught Rust panic safely -> {e}")
except Exception as e:
    print(f"INFO: babylon60 C-extension not pre-compiled locally: {e}")

from src.bft_sqlite import BFTSQLite
bft = BFTSQLite()
print("BFTSQLite instanciado exitosamente.")

