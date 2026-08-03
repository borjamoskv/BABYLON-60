import hashlib

class CausalWitness:
    def __init__(self, previous_hash: str):
        self.previous_hash = previous_hash

class CrystallizedEvent:
    def __init__(self, payload: str, causal_proof: CausalWitness, lamport_t: int):
        self.payload = payload
        self.causal_proof = causal_proof
        self.lamport_t = lamport_t
        self.hash = self._compute_hash()
    
    def _compute_hash(self):
        # 32-byte hash commitment
        data = f"{self.causal_proof.previous_hash}:{self.lamport_t}:{self.payload}".encode('utf-8')
        return hashlib.blake2b(data, digest_size=32).hexdigest()

class MotorCausal:
    def __init__(self):
        # Genesis block
        self.head_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        self.current_lamport = 0
        self.ledger = []

    def mutate_state(self, event: CrystallizedEvent):
        """
        Falsabilidad Estructural (INV_BFT_04 / Válvula Termodinámica):
        El Motor rechaza en O(1) cualquier evento fuera del Cono de Luz Causal.
        """
        # 1. Verificación del Causal Light Cone (Topología Hash)
        if event.causal_proof.previous_hash != self.head_hash:
            raise ValueError(
                f"[BYZANTINE COLLISION] Evento fuera del cono de luz causal.\n"
                f"Esperado (Head): {self.head_hash[:8]}...\n"
                f"Recibido (Proof): {event.causal_proof.previous_hash[:8]}..."
            )
            
        # 2. Verificación del Tiempo de Lamport
        if event.lamport_t <= self.current_lamport:
            raise ValueError(
                f"[CAUSAL DRIFT] Violación del vector temporal de Lamport.\n"
                f"Reloj del Motor: {self.current_lamport}\n"
                f"Reloj del Evento: {event.lamport_t}"
            )
            
        # El estado cristaliza
        self.current_lamport = event.lamport_t
        self.head_hash = event.hash
        self.ledger.append(event)
        print(f"[O(1) CRYSTALLIZED] Evento aceptado | L-Time: {self.current_lamport} | Hash: {self.head_hash[:8]}...")

if __name__ == "__main__":
    motor = MotorCausal()
    
    print("--- 1. ESCENARIO VÁLIDO (Dentro del Cono de Luz) ---")
    event_1 = CrystallizedEvent(
        payload="Mutación A", 
        causal_proof=CausalWitness(motor.head_hash), 
        lamport_t=motor.current_lamport + 1
    )
    motor.mutate_state(event_1)
    
    event_2 = CrystallizedEvent(
        payload="Mutación B", 
        causal_proof=CausalWitness(motor.head_hash), 
        lamport_t=motor.current_lamport + 1
    )
    motor.mutate_state(event_2)
    
    print("\n--- 2. ESCENARIO BYZANTINE (Violación de Hash Topológico) ---")
    # Intentamos inyectar un evento basándonos en un hash antiguo (split-brain)
    event_3_byz = CrystallizedEvent(
        payload="Mutación C (Byzantine)", 
        causal_proof=CausalWitness(event_1.hash), # Usamos el hash antiguo
        lamport_t=motor.current_lamport + 1
    )
    try:
        motor.mutate_state(event_3_byz)
    except ValueError as e:
        print(f"FALSACIÓN EXITOSA (O(1) Drop): {e}")

    print("\n--- 3. ESCENARIO NTP/POSIX DRIFT (Violación de Lamport) ---")
    # Simulamos un NTP desfasado que manda un tiempo de Lamport antiguo o repetido
    event_4_drift = CrystallizedEvent(
        payload="Mutación D (NTP Drift)", 
        causal_proof=CausalWitness(motor.head_hash), 
        lamport_t=motor.current_lamport # El tiempo no avanza
    )
    try:
        motor.mutate_state(event_4_drift)
    except ValueError as e:
        print(f"FALSACIÓN EXITOSA (O(1) Drop): {e}")
        
    print("\n[✔] Axioma Temporal F60 validado empíricamente.")
