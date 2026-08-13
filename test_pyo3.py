import logging
import os
import sys

logging.basicConfig(level=logging.INFO)
# Agregar src al path
sys.path.insert(0, os.path.abspath('.'))

try:
    import babylon60
    print(f"SUCCESS: Direct babylon60 import -> {babylon60.kernel_status()}")
except Exception as e:
    print(f"ERROR: Importing babylon60 directly: {e}")

from src.bft_sqlite import BFTSQLite
# Instanciar el BFT que ahora debe reportar en el log la llamada a Rust
bft = BFTSQLite()
print("BFTSQLite instanciado exitosamente.")
