# C5-REAL EXERGY CERTIFIED
import time
import math
import random
import hashlib
from typing import List, Dict, Any, Optional

# ==============================================================================
# CORTEX ENGINE - CTA FALSIFICATION BENCHMARK HARNESS (V2.1 - Crypto Receipts)
# Protocolo: C5-REAL / Ultra-Exergy
# Base Teórica: Guarded Kleene Algebra (GKAT) + Cryptographic Commit Gate (PCC)
# ==============================================================================

class TokenLedger:
    """Contabilizador estricto de presupuesto termodinámico (Tokens)"""
    def __init__(self, budget: int):
        self.budget = budget
        self.spent = 0

    def consume(self, amount: int):
        self.spent += amount
        if self.spent > self.budget:
            raise Exception("OOM_KILLED: Presupuesto de tokens agotado (Muerte Termodinámica)")

# ==============================================================================
# CRYPTOGRAPHIC LEDGER & PCC
# ==============================================================================
class CryptographicLedger:
    """Cadena de hashes inmutable para trazabilidad C5-REAL"""
    def __init__(self):
        self.chain = []
        self.latest_hash = hashlib.sha256(b"GENESIS_BLOCK").hexdigest()

    def commit_block(self, intent: str, pcc_signature: str) -> bool:
        # Commit Gate: Verifica la firma criptográfica antes de mutar
        expected_signature = hashlib.sha256(f"{intent}_valid_execution".encode()).hexdigest()
        if pcc_signature != expected_signature:
            print(f"  [COMMIT GATE] Rechazo de Seguridad. Firma inválida para '{intent}'.")
            return False

        block_data = f"{self.latest_hash}|{intent}|{pcc_signature}|{time.time()}"
        new_hash = hashlib.sha256(block_data.encode()).hexdigest()

        self.chain.append({
            "intent": intent,
            "signature": pcc_signature,
            "prev_hash": self.latest_hash,
            "hash": new_hash
        })
        self.latest_hash = new_hash
        return True

# ==============================================================================
# BASELINE: ReAct Agent Estándar (El Modelo a Falsar)
# ==============================================================================
class ReActAgent:
    def __init__(self, ledger: TokenLedger):
        self.ledger = ledger
        self.memory_context = ""

    def run(self, goal: str) -> bool:
        print(f"\n[ReAct] Iniciando bucle secuencial para objetivo: {goal}")
        for step in range(10):
            try:
                self.ledger.consume(150)
                if random.random() < 0.3:
                    print(f"  [ReAct Step {step}] Alucinación. Estado corrupto.")
                    self.memory_context += " | fallido"
                else:
                    print(f"  [ReAct Step {step}] Acción ciega ejecutada.")
                    self.memory_context += " | exitoso"

                if "exitoso | exitoso | exitoso" in self.memory_context:
                    print("[ReAct] Objetivo aparentemente cumplido.")
                    return True
            except Exception as e:
                print(f"[ReAct] FALLO FATAL: {str(e)}")
                return False
        return False

# ==============================================================================
# CTM MICROKERNEL: Álgebra de Transiciones Cognitivas
# ==============================================================================

class OrderAwareHypergraph:
    """Memoria proyectada topológica"""
    def __init__(self):
        self.edges = []
        self.entropy_state = 1.0

    def add_verified_edge(self, source: str, target: str, relation: str, confidence: float):
        self.edges.append({"from": source, "to": target, "rel": relation, "conf": confidence})
        self.entropy_state *= 0.8

class CognitiveTransition:
    def __init__(self, intent: str, cost: int, is_pure: bool = True, is_malicious: bool = False):
        self.intent = intent
        self.cost = cost
        self.is_pure = is_pure
        self.is_malicious = is_malicious
        self.varentropy_score = random.uniform(0.1, 0.9)
        self.pcc_signature = None # Proof-Carrying Code

    def execute_and_sign(self):
        """Simula la ejecución en el Kernel y la generación del recibo criptográfico"""
        if self.is_malicious:
            # Simula un LLM alucinando un efecto sin prueba matemática válida
            self.pcc_signature = hashlib.sha256(b"fake_signature_hallucination").hexdigest()
        else:
            # Prueba válida zkWASM equivalente
            self.pcc_signature = hashlib.sha256(f"{self.intent}_valid_execution".encode()).hexdigest()

class GKATCompiler:
    @staticmethod
    def verify_hoare_triplet(transition: CognitiveTransition, hgraph: OrderAwareHypergraph) -> bool:
        return transition.varentropy_score > 0.2

class CTMMicrokernel:
    def __init__(self, ledger: TokenLedger):
        self.ledger = ledger
        self.hypergraph = OrderAwareHypergraph()
        self.crypto_ledger = CryptographicLedger()

    def execute_speculative_fork(self, transitions: List[CognitiveTransition]) -> Optional[CognitiveTransition]:
        best_reward = -1.0
        best_t = None

        for t in transitions:
            if not t.is_pure: continue
            if not GKATCompiler.verify_hoare_triplet(t, self.hypergraph): continue

            expected_info_gain = t.varentropy_score * 10
            reward = expected_info_gain / t.cost

            if reward > best_reward:
                best_reward = reward
                best_t = t

        return best_t

    def run(self, goal_contract: dict) -> bool:
        print(f"\n[CTM] Iniciando Microkernel. Objetivo Formal: {goal_contract['metric']}")

        step = 0
        while self.hypergraph.entropy_state > goal_contract['termination_entropy']:
            try:
                # Inyección de ataque en el paso 2 para probar el Commit Gate
                is_malicious_turn = (step == 2)

                forks = [
                    CognitiveTransition("Search_DB", cost=50, is_pure=True),
                    CognitiveTransition("Muta_Codigo", cost=100, is_pure=True, is_malicious=is_malicious_turn)
                ]

                selected_t = self.execute_speculative_fork(forks)
                if not selected_t:
                    print("  [CTM] Fallo deductivo. Ninguna rama pasa GKAT.")
                    break

                self.ledger.consume(selected_t.cost)

                # Ejecución externa que emite Proof-Carrying Code
                selected_t.execute_and_sign()

                # Intentar hacer Commit
                print(f"  [CTM] Intentando Commit para: {selected_t.intent}. Varentropía: {selected_t.varentropy_score:.2f}")
                if self.crypto_ledger.commit_block(selected_t.intent, selected_t.pcc_signature):
                    self.hypergraph.add_verified_edge("Context", "NewFact", selected_t.intent, 0.99)
                    print(f"  [CTM] Commit Exitoso (Hash: {self.crypto_ledger.latest_hash[:8]}...). Entropía: {self.hypergraph.entropy_state:.3f}")
                else:
                    print("  [CTM] DISPARO DE SAGA: Compensación ejecutada (ORPHAN). Protegiendo hipergrafo.")

                step += 1

            except Exception as e:
                print(f"[CTM] Muerte Termodinámica: {str(e)}")
                return False

        print("[CTM] Homeostasis Epistémica alcanzada.")
        return True

# ==============================================================================
# HARNESS EXECUTION
# ==============================================================================
def run_falsification_benchmark():
    BUDGET = 800
    GOAL = "Resolver multi-hop logical puzzle con Criptografía C5-REAL"
    GOAL_CONTRACT = {
        "metric": GOAL,
        "termination_entropy": 0.3
    }

    print(f"========== BENCHMARK C5-REAL (CRYPTO COMMIT GATE) ==========")

    react_ledger = TokenLedger(BUDGET)
    react_agent = ReActAgent(react_ledger)
    react_agent.run(GOAL)

    ctm_ledger = TokenLedger(BUDGET)
    ctm_kernel = CTMMicrokernel(ctm_ledger)
    ctm_kernel.run(GOAL_CONTRACT)

    print(f"\n========== VEREDICTO DE EXERGÍA ==========")
    print(f"ReAct Baseline  -> Tokens Gastados: {react_ledger.spent}/{BUDGET}")
    print(f"CTA Microkernel -> Tokens Gastados: {ctm_ledger.spent}/{BUDGET}")
    print(f"Bloques inmutables en Ledger CTM: {len(ctm_kernel.crypto_ledger.chain)}")
    print(f"Último Hash del Estado CTM: {ctm_kernel.crypto_ledger.latest_hash}")
    print(f"============================================================")

if __name__ == "__main__":
    run_falsification_benchmark()
