# C5-REAL EXERGY CERTIFIED
import sys
from guard import enforce_invariant

def main():
    print("[CORTEX] Testeando BFT Vanguard Guard...")
    print("[CORTEX] Comprobando invariante válido...")
    enforce_invariant(True, "VALID_STATE")
    print("[PASS] Invariante válido sobrevivió.")

    print("[CORTEX] Simulando colapso de invariante estructural...")
    # This will trigger abort() and crash the process
    enforce_invariant(False, "STOCHASTIC_HALLUCINATION_DETECTED")

    # We should NEVER reach this line
    print("[FATAL ERROR] El Guard falló en matar el proceso. Green Theater detectado.")
    sys.exit(1)

if __name__ == "__main__":
    main()
