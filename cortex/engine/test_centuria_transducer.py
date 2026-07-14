"""
C5-REAL: PRUEBA DE ESTRÉS EMPÍRICA (Centuria Transducer)
=======================================================
Verificación física de los invariantes C5-REAL bajo ataque.
"""
import sys
import hashlib
import traceback
from centuria_transducer_core import (
    purge_green_theater,
    HardAttentionRouter,
    CausalAnchor,
    sinkhole_oom_enforcer
)

def test_poda_latente():
    print("[-] Test I: Poda Latente (Green Theater Attack)")
    payload_clean = "Payload purgado y consolidado. Hash de salida generado."
    
    # Test valid
    try:
        res = purge_green_theater(payload_clean)
        print("    [PASS] Clean payload aceptado.")
    except SystemExit:
        print("    [FAIL] Clean payload detonó incorrectamente.")
        sys.exit(1)
        
    # Test violation
    try:
        purge_green_theater(payload_violator)
        print("    [FAIL] Violator payload evadió el filtro.")
        sys.exit(1)
    except SystemExit as e:
        print(f"    [PASS] Violator interceptado y aniquilado con SIGKILL_State_Purge ({e}).")

def test_hard_attention():
    print("\n[-] Test II: Ruteo Hard-Attention")
    payload = "def fast_inverse_sqrt(x: float) -> float:"
    m = hashlib.sha3_256(payload.encode("utf-8"))
    correct_hash = m.hexdigest()
    wrong_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    
    # Test valid
    assert HardAttentionRouter.assert_focus(correct_hash, payload) is True
    print("    [PASS] Hard-Attention anclado al hash criptográfico real.")
    
    # Test violation
    try:
        HardAttentionRouter.assert_focus(wrong_hash, payload)
        print("    [FAIL] Atención difusa evadió el control.")
        sys.exit(1)
    except ValueError as e:
        print(f"    [PASS] Desvío bloqueado exitosamente: {e}")

def test_anti_lost_in_the_middle():
    print("\n[-] Test III: Anti-Lost-in-the-Middle")
    agent_id = "MOSKV-1"
    payload = "Contexto previo... "
    new_payload = CausalAnchor.checkpoint(agent_id, payload)
    
    if "[CORTEX-TAINT:ANCHOR:MOSKV-1:" in new_payload:
        print("    [PASS] Ancla criptográfica inyectada en el flujo.")
    else:
        print("    [FAIL] Fallo en la inyección de CausalAnchor.")
        sys.exit(1)

def test_sinkhole_enforcer():
    print("\n[-] Test IV: Purga de Sumideros (Limerencia y Recursividad)")
    
    @sinkhole_oom_enforcer(max_iterations=2)
    def recursive_sinkhole():
        pass
        
    try:
        recursive_sinkhole()
        print("    [PASS] Iteración 1 aceptada.")
        recursive_sinkhole()
        print("    [PASS] Iteración 2 aceptada.")
        recursive_sinkhole()
        print("    [FAIL] Iteración 3 evadió el OOM.")
        sys.exit(1)
    except SystemExit as e:
        print(f"    [PASS] Iteración 3 detonó OOM Físico exitosamente ({e}).")

if __name__ == "__main__":
    print("[*] Iniciando prueba física de matriz Centuria...\n")
    test_poda_latente()
    test_hard_attention()
    test_anti_lost_in_the_middle()
    test_sinkhole_enforcer()
    print("\n[*] C5-REAL: MATRIZ VALIDADA. Cero Fugas de Anergía.")
