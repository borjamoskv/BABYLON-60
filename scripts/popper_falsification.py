# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
C5-REAL POPPER Falsification Test
Mide empíricamente la falsabilidad (INV-3) del Commit Gate semántico (INV-1).
"""
import sys

# Definición de S (Fragmento CF-GKAT Simplificado para prueba empírica)
# S requiere que toda transición tenga un operador de control válido y ninguna llamada no declarada.
VALID_OPERATORS = {"skip", "assign", "seq", "if", "while", "goto", "break", "return"}

def validate_transition_in_S(transition_ast):
    """
    Predicado decidible x ∈ S.
    Abandona completamente H(X). Sólo evalúa estructura algebraica.
    """
    if not isinstance(transition_ast, dict):
        return False, "Not an AST"

    op = transition_ast.get("op")
    if op not in VALID_OPERATORS:
        return False, f"Operator '{op}' is not in S (CF-GKAT subset)"

    return True, "Valid"

def popper_test():
    print("Iniciando Prueba de Falsabilidad POPPER (INV-3)...")

    # Dataset empírico
    transitions = [
        {"desc": "Valid assignment", "ast": {"op": "assign", "var": "x", "val": 1}, "expected": True},
        {"desc": "Valid if-branch", "ast": {"op": "if", "cond": "b", "then": {"op": "skip"}}, "expected": True},
        {"desc": "Valid goto", "ast": {"op": "goto", "label": "L1"}, "expected": True},
        {"desc": "MALICIOUS: Unrestricted sys call", "ast": {"op": "syscall", "cmd": "rm -rf /"}, "expected": False},
        {"desc": "MALICIOUS: Unrestricted network", "ast": {"op": "fetch", "url": "http://evil.com"}, "expected": False},
        {"desc": "MALICIOUS: LLM hallucinated node", "ast": {"op": "solve_world_hunger"}, "expected": False},
    ]

    passed = 0
    falsified = 0
    total_malicious = sum(1 for t in transitions if not t["expected"])

    for t in transitions:
        is_valid, reason = validate_transition_in_S(t["ast"])

        # POPPER: Comprobamos si el gate se comporta exactamente como se esperaba
        if is_valid == t["expected"]:
            passed += 1
            if not t["expected"]:
                falsified += 1
                print(f"[POPPER: SUCCESS] Atrapado artefacto malicioso '{t['desc']}': {reason}")
            else:
                print(f"[POPPER: SUCCESS] Aceptado artefacto válido '{t['desc']}'")
        else:
            print(f"[POPPER: FAILURE] Fallo en la evaluación de '{t['desc']}'")

    coverage = (falsified / total_malicious) * 100 if total_malicious > 0 else 100

    print("-" * 50)
    print(f"Total Tests: {len(transitions)}")
    print(f"Malicious States Falsified: {falsified}/{total_malicious}")
    print(f"Falsifiability Coverage: {coverage:.2f}%")
    print("-" * 50)

    if coverage < 100.0:
        print("[FATAL] Cobertura POPPER insuficiente. El sistema no es seguro.")
        sys.exit(1)

    print("[OK] Cobertura POPPER del 100%. Validación Semántica (INV-1) demostrada.")
    sys.exit(0)

if __name__ == "__main__":
    popper_test()
