# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import sys
import os

# Ensure the module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from babylon60.bft.bayesian_swarm import BayesianSwarm


def run_poc():
    print("=== [Causal-Determinist] PoC: Logarithmic Opinion Pooling (LogOP) Veto ===")

    # Simulate a Swarm of 3 Agents (Experts)
    swarm = BayesianSwarm(["Agent_Alpha", "Agent_Beta", "Agent_Gamma"])

    # Case 1: All agree on high probability for Mutation_A
    print("\n--- Escenario 1: Consenso Estándar ---")
    opinions_1 = {
        "Agent_Alpha": {"Mutation_A": 0.9, "Mutation_B": 0.1},
        "Agent_Beta": {"Mutation_A": 0.85, "Mutation_B": 0.15},
        "Agent_Gamma": {"Mutation_A": 0.95, "Mutation_B": 0.05},
    }
    result_1 = swarm.logarithmic_opinion_pool(opinions_1)
    print("Opiniones:", opinions_1)
    print("LogOP Agregado:", result_1)

    # Case 2: Byzantine/Veto (Agent_Gamma discovers a fatal flaw in Mutation_A and assigns p=0.0)
    print("\n--- Escenario 2: Absolute Veto (Fallo Rápido) ---")
    opinions_2 = {
        "Agent_Alpha": {"Mutation_A": 0.99, "Mutation_B": 0.01},  # Highly confident
        "Agent_Beta": {"Mutation_A": 0.99, "Mutation_B": 0.01},  # Highly confident
        "Agent_Gamma": {"Mutation_A": 0.00, "Mutation_B": 1.00},  # VETO ABSOLUTO
    }
    result_2 = swarm.logarithmic_opinion_pool(opinions_2)
    print("Opiniones:", opinions_2)
    print("LogOP Agregado:", result_2)

    if result_2.get("Mutation_A", 1.0) == 0.0:
        print("\n[SUCCESS] INV_BFT_LOGOP Verificado: El veto colapsó matemáticamente la alucinación bizantina a 0.0.")
    else:
        print("\n[FAILED] El veto no fue respetado.")


if __name__ == "__main__":
    run_poc()
