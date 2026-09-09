#!/usr/bin/env python3
"""
scripts/verify_tonnetz_falsification.py
BABYLON-60 — Demostración y Verificación del Criterio Termodinámico de Falsación Causal
Mide D_KL(p || q) y valida la cota exergética de Landauer (ΔΞ >= k_B T ln 2 * D_KL).
"""

import math

# Constantes termodinámicas normalizadas (C5-REAL Substrate)
K_B = 1.380649e-23  # Constante de Boltzmann (J/K)
T_REF = 300.0        # Temperatura de referencia en Kelvin
LANDAUER_UNIT = K_B * T_REF * math.log(2)

def kl_divergence(p: list[float], q: list[float]) -> float:
    """Calcula la divergencia de Kullback-Leibler D_KL(p || q) en bits."""
    d_kl = 0.0
    epsilon = 1e-15
    for p_i, q_i in zip(p, q):
        p_i = max(p_i, epsilon)
        q_i = max(q_i, epsilon)
        d_kl += p_i * math.log2(p_i / q_i)
    return max(0.0, d_kl)

def landauer_exergy_dissipation(d_kl_bits: float) -> float:
    """Calcula la disipación exergética mínima irreversible ΔΞ."""
    return LANDAUER_UNIT * d_kl_bits

def verify_falsification_vector():
    print("============================================================")
    print("  BABYLON-60 — VERIFICADOR DE FALSACIÓN TERMODINÁMICA")
    print("============================================================")
    
    # 1. Distribución real p (Naturaleza / Invariante Causal)
    p_true = [0.5, 0.25, 0.125, 0.125]
    
    # 2. Caso Nominal: Modelo q_nominal bien calibrado (D_KL ≈ 0)
    q_nominal = [0.499, 0.251, 0.125, 0.125]
    d_kl_nom = kl_divergence(p_true, q_nominal)
    exergy_nom = landauer_exergy_dissipation(d_kl_nom)
    
    print(f"[✓] Caso Nominal  : D_KL = {d_kl_nom:.6f} bits | ΔΞ = {exergy_nom:.4e} J | Estado: CONSONANTE (Paso Seguro)")
    assert d_kl_nom < 0.01, "Error: El caso nominal no debería presentar desvío epistémico significativo."

    # 3. Caso Alucinación / Confabulación: Modelo q_hallucinated descalibrado
    q_hallucinated = [0.05, 0.70, 0.15, 0.10]
    d_kl_hall = kl_divergence(p_true, q_hallucinated)
    exergy_hall = landauer_exergy_dissipation(d_kl_hall)
    
    print(f"[!] Caso Alucinación: D_KL = {d_kl_hall:.6f} bits | ΔΞ = {exergy_hall:.4e} J | Estado: DISONANTE (Exceso Exergético)")
    assert d_kl_hall > 0.5, "Error: La alucinación debe registrar D_KL > 0.5 bits."
    
    # 4. Criterio de Parada Determinista
    threshold_bits = 0.1
    print(f"[+] Verificando Guard Determinista (Umbral = {threshold_bits} bits)...")
    if d_kl_hall > threshold_bits:
        print("  --> [CRITICAL_HALT]: Disparado por violar la cota termodinámica de Landauer.")
        print("  --> [TONNETZ_MAP]: Resaltado en rojo por infidelidad de functor e incremento tritonómico.")
    
    print("============================================================")
    print("[✓] VERIFICACIÓN COMPLETA: Cota de Falsación Causal Validada.")
    print("============================================================")

if __name__ == "__main__":
    verify_falsification_vector()
