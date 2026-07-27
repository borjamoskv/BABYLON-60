import json
import hashlib
import secrets

# ============================================================
# Utilidades básicas
# ============================================================

def canon(obj):
    """
    Serialización canónica de objetos.
    La usamos como "lenguaje de programas".
    """
    return json.dumps(
        obj,
        separators=(",", ":"),
        sort_keys=True,
        ensure_ascii=False,
    )

def byte_length(s: str) -> int:
    return len(s.encode("utf-8"))

def program_length(prog) -> int:
    """
    Longitud del programa en bytes.
    En esta toy-machine, un programa es un objeto JSON serializable.
    """
    return byte_length(canon(prog))

# ============================================================
# Generación de una cadena "aparentemente aleatoria"
# ============================================================

def expand_seed(seed: str, chars: int) -> str:
    """
    Expande una semilla corta en una cadena larga usando SHA-256.
    """
    if chars <= 0:
        return ""

    out = []
    total = 0
    i = 0

    while total < chars:
        block = hashlib.sha256(f"{seed}:{i}".encode("utf-8")).hexdigest()
        out.append(block)
        total += len(block)
        i += 1

    return "".join(out)[:chars]

# ============================================================
# Teoría de juguete
# ============================================================

def derive_theorem(axiom):
    """
    Regla de inferencia de juguete.
    """
    kind = axiom.get("kind")

    if kind == "KGT_SEED":
        x = expand_seed(axiom["seed"], axiom["chars"])
        return {
            "kind": "KGT",
            "x": x,
            "n": axiom["n"],
        }

    if kind == "KGT":
        return axiom

    return None

def enumerate_theorems(axioms):
    for axiom in axioms:
        theorem = derive_theorem(axiom)
        if theorem is not None:
            yield theorem

def find_proven_KGT(axioms, N):
    for theorem in enumerate_theorems(axioms):
        if theorem.get("kind") == "KGT" and theorem.get("n", 0) >= N:
            return theorem
    return None

# ============================================================
# Máquina universal de juguete
# ============================================================

def run_program(prog):
    ptype = prog.get("type")

    if ptype == "print":
        return prog["value"]

    if ptype == "chaitin_search":
        axioms = prog["theory"]["axioms"]
        N = prog["N"]

        for theorem in enumerate_theorems(axioms):
            if theorem.get("kind") == "KGT" and theorem.get("n", 0) >= N:
                return theorem["x"]
        return None

    raise ValueError(f"tipo de programa no soportado: {ptype}")

# ============================================================
# Programa diagonal de Chaitin
# ============================================================

def make_chaitin_program(axioms, N):
    return {
        "type": "chaitin_search",
        "theory": {"axioms": axioms},
        "N": N,
    }

def diagonal_N(axioms, margin=16):
    N = 1
    while True:
        prog = make_chaitin_program(axioms, N)
        L = program_length(prog)

        if N > L:
            return N, prog, L
        N = L + margin

# ============================================================
# Demostración
# ============================================================

def demo():
    seed = secrets.token_hex(16)
    chars = 4000
    claimed_bound = 1_000_000

    axioms = [
        {
            "kind": "KGT_SEED",
            "seed": seed,
            "chars": chars,
            "n": claimed_bound,
        }
    ]

    theory_len = program_length({"theory": {"axioms": axioms}})
    N, prog, L = diagonal_N(axioms, margin=16)

    if N > claimed_bound:
        raise ValueError("claimed_bound demasiado pequeño; auméntalo")

    theorem = find_proven_KGT(axioms, N)
    assert theorem is not None, "La teoría no prueba ningún K(x) >= N"

    x = theorem["x"]
    y = run_program(prog)

    literal_prog = {"type": "print", "value": x}
    literal_len = program_length(literal_prog)

    print("=== Teoría finita T ===")
    print(f"Semilla incluida en axiomas: {seed}")
    print(f"Longitud de la descripción de T: {theory_len} bytes")
    print(f"T afirma: K(x) > {claimed_bound}")
    print()

    print("=== Programa diagonal P_N ===")
    print(f"N: {N}")
    print(f"Longitud |P_N|: {L} bytes")
    print(f"¿P_N imprime x? {y == x}")
    print()

    print("=== Objeto x ===")
    print(f"Longitud de x: {len(x)}")
    print(f"Primeros 64 caracteres: {x[:64]}...")
    print(f"Cota superior de K(x) vía P_N: {L}")
    print(f"Cota superior de K(x) vía programa literal: {literal_len}")
    print()

    assert y == x, "P_N no imprime el x que la teoría prueba"
    assert L < N, "No se cumplió |P_N| < N"
    assert N <= claimed_bound

    print("=== Contradicción informacional ===")
    print(f"T prueba K(x) > {claimed_bound}.")
    print(f"Pero P_N es un programa de {L} bytes que imprime x.")
    print(f"Por tanto K(x) <= {L} < {N} <= {claimed_bound}.")
    print("La teoría no puede ser consistente y correcta a la vez.")

if __name__ == "__main__":
    demo()
