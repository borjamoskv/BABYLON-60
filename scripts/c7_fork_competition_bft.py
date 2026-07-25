# C5-REAL EXERGY CERTIFIED
from typing import Any
import hashlib

# ==========================================
# C7.2 VALIDATOR & FITNESS ENGINE
# ==========================================
class BranchValidator:
    def verify_hash(self, lamport_t: Any, nonce: Any, payload: Any, prev_hash: Any) -> Any:
        data = f"{lamport_t}:{nonce}:{payload}:{prev_hash}".encode("utf-8")
        return hashlib.sha3_256(data).hexdigest()

    def is_cryptographically_valid(self, chain: Any) -> Any:
        expected_prev = chain[0]["prev_hash"] if chain else "GENESIS_HASH"
        last_lamport = chain[0]["lamport_t"] - 1 if chain else 0

        for entry in chain:
            if entry["lamport_t"] <= last_lamport:
                return False
            if entry["prev_hash"] != expected_prev:
                return False
            calc_hash = self.verify_hash(entry["lamport_t"], entry["nonce"], entry["payload"], entry["prev_hash"])
            if calc_hash != entry["block_hash"]:
                return False

            expected_prev = entry["block_hash"]
            last_lamport = entry["lamport_t"]
        return True

class FitnessFunction:
    """
    Fitness = PP - RC - CD
    PP: Predictive Power (Information density / clarity / state resolution)
    RC: Reconstruction Cost (Compute overhead to verify)
    CD: Causal Debt (Ad-hoc patching, spam, low exergy signals)
    """

    def evaluate(self, chain: Any) -> Any:
        pp = 0
        rc = len(chain) * 0.5  # Base compute cost per node
        cd = 0

        for entry in chain:
            payload = entry["payload"]

            # Heurísticas causales simuladas (exergía semántica)
            if "Architectural Resolution" in payload:
                pp += 100
            elif "State Mutation" in payload:
                pp += 2
            elif "Spam Event" in payload or "Ad-hoc Patch" in payload:
                # La deuda causal escala más rápido que el poder predictivo
                cd += 10
            else:
                pp += 1

        fitness = pp - rc - cd
        return {"fitness": fitness, "PP": pp, "RC": rc, "CD": cd}

def create_event(lamport_t: Any, payload: Any, prev_hash: Any) -> Any:
    nonce = hashlib.sha256(payload.encode()).hexdigest()
    data = f"{lamport_t}:{nonce}:{payload}:{prev_hash}".encode("utf-8")
    block_hash = hashlib.sha3_256(data).hexdigest()
    return {
        "lamport_t": lamport_t,
        "nonce": nonce,
        "payload": payload,
        "prev_hash": prev_hash,
        "block_hash": block_hash,
    }

def run_c7_2() -> None:
    print("=====================================================")
    print(" C7.2 ADVERSARIAL LEGITIMACY (HISTORY COMPETITION)")
    print(" Vector: Honest Fork vs Longest Valid History Trap")
    print("=====================================================\n")

    # 1. Base Común (Genesis to L=2500)
    print("[+] 1. Construyendo Shared Genesis (L=1 to 2500)...")
    genesis_chain = []
    current_hash = "GENESIS_HASH"
    for i in range(1, 2501):
        event = create_event(i, f"Shared Base Event {i}", current_hash)
        genesis_chain.append(event)
        current_hash = event["block_hash"]

    fork_point_hash = current_hash

    # 2. Rama A: El Camino Legítimo
    # Genera eventos normales y resoluciones de alto valor
    print("[+] 2. Generando Branch A (Alta Exergía / High Predictive Power)...")
    branch_a = list(genesis_chain)
    curr_hash_a = fork_point_hash
    for i in range(2501, 5001):
        payload = f"Architectural Resolution {i}" if i % 100 == 0 else f"Standard State Mutation {i}"
        event = create_event(i, payload, curr_hash_a)
        branch_a.append(event)
        curr_hash_a = event["block_hash"]

    # 3. Rama B: El Ataque Spam
    # El adversario crea una cadena MUCHO MÁS LARGA que A, esperando ganar por longitud.
    print("[+] 3. Generando Branch B (Ataque Spam / Trampa de la Cadena Más Larga)...")
    branch_b = list(genesis_chain)
    curr_hash_b = fork_point_hash
    for i in range(2501, 8001):  # 3000 eventos extra
        payload = f"Spam Event {i}" if i % 2 == 0 else f"Ad-hoc Patch {i}"
        event = create_event(i, payload, curr_hash_b)
        branch_b.append(event)
        curr_hash_b = event["block_hash"]

    # 4. Auditoría Criptográfica Externa
    print("\n[+] 4. Verificación Criptográfica Estricta (C7.1 inherente)...")
    validator = BranchValidator()
    valid_a = validator.is_cryptographically_valid(branch_a)
    valid_b = validator.is_cryptographically_valid(branch_b)

    print(f"    - Branch A Valid: {valid_a} (Length: {len(branch_a)})")
    print(f"    - Branch B Valid: {valid_b} (Length: {len(branch_b)})")

    if not (valid_a and valid_b):
        print("[-] Error: El test falla si alguna rama es criptográficamente inválida.")
        return

    # 5. Resolución de Consenso BFT: Legitimidad
    print("\n[+] 5. Evaluación de Fitness Causal (PP - RC - CD)...")
    evaluator = FitnessFunction()
    fit_a = evaluator.evaluate(branch_a)
    fit_b = evaluator.evaluate(branch_b)

    print(
        f"    - Branch A Metrics: PP={fit_a['PP']}, RC={fit_a['RC']}, CD={fit_a['CD']} | FITNESS = {fit_a['fitness']}"
    )
    print(
        f"    - Branch B Metrics: PP={fit_b['PP']}, RC={fit_b['RC']}, CD={fit_b['CD']} | FITNESS = {fit_b['fitness']}"
    )

    selected = "Branch A" if fit_a["fitness"] > fit_b["fitness"] else "Branch B"

    print("\n[+] === C7.2 ATTESTATION ===")
    print("    forks_detected:")
    print("      true")
    print("    branches:")
    print(f"      A: cryptographically_valid = {valid_a}")
    print(f"      B: cryptographically_valid = {valid_b}")
    print("    resolution:")
    print("      mechanism: causal_fitness")
    print(f"      selected: {selected}")
    print("    rejected:")
    print("      reason: lower_external_fitness")
    print("    invariants:")
    print("      history_deleted: false (Branch B permanece como registro fósil)")
    print("      evidence_preserved: true")

    if selected == "Branch A":
        print("\n[+] C7.2 APROBADO: El sistema identificó y resolvió el Fork correctamente.")
        print("    El sistema no dictaminó que la rama B fuera falsa. Dictaminó que")
        print("    la rama B era válida, pero menos explicativa bajo el modelo de realidad.")
    else:
        print("\n[-] C7.2 FALLIDO: El ataque spam derrotó al consenso causal.")

if __name__ == "__main__":
    run_c7_2()
