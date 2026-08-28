# C5-REAL EXERGY CERTIFIED
import os
import sys

def get_bft_key() -> str:
    """
    Recupera CORTEX_BFT_KEY del entorno en tiempo de ejecución.
    Invariante Ω25: ZERO STATIC HMAC FALLBACK.
    Si la clave no está definida, dispara purga inmediata del proceso.
    """
    key = os.environ.get("CORTEX_BFT_KEY")
    if not key:
        print(
            "EpistemicHalt: CORTEX_BFT_KEY no definida en el entorno (Ω25). Terminación de seguridad.", file=sys.stderr
        )
        # Ω26: FAIL-FAST PURGE
        # En caso de no tener la clave, fail-fast total.
        sys.exit(1)
    return key
