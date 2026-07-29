"""
[C5-REAL] Empirical Calibration Tool for Popperian Shannon Entropy Thresholds.

Performs empirical statistical analysis over workspace code/docs vs synthetic hype
to remove the UNBACKED status on MIN_ENTROPY and MAX_ENTROPY per INV_INGESTA_08.
"""

import os
import sys
import math
from typing import List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from babylon60.core.popperian_filter import shannon_entropy

TECHNICAL_CORPUS_PATHS = [
    "babylon60/database/core.py",
    "babylon60/bft/bayesian_swarm.py",
    "strike_rs/src/atms.rs",
    "README.md",
    "AGENTS.md"
]

HYPE_CORPUS_SAMPLES = [
    "Unlock 100x passive income with this revolutionary game changer system!",
    "Scale to the moon using next-generation AI disruption synergy 6-figure secret.",
    "This 10x paradigm shift will transform your workflow into massive profit overnight.",
    "Delve into unpacking the ultimate silver bullet no-brainer growth hack."
]

def calculate_stats(values: List[float]) -> Tuple[float, float, float, float]:
    """Calculates mean, stddev, min, max."""
    if not values:
        return 0.0, 0.0, 0.0, 0.0
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    stddev = math.sqrt(variance)
    return mean, stddev, min(values), max(values)

def run_calibration():
    print("=== [C5-REAL] Calibración Empírica de Entropía Popperiana (INV_INGESTA_08) ===")
    
    tech_entropies = []
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    for rel_path in TECHNICAL_CORPUS_PATHS:
        full_path = os.path.join(root_dir, rel_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                ent = shannon_entropy(content)
                tech_entropies.append(ent)
                print(f"[TECHNICAL CORPUS] {rel_path}: Entropy = {ent:.4f}")
        else:
            print(f"[WARN] File not found: {rel_path}")
            
    hype_entropies = [shannon_entropy(text) for text in HYPE_CORPUS_SAMPLES]
    for idx, ent in enumerate(hype_entropies):
        print(f"[HYPE CORPUS] Sample {idx+1}: Entropy = {ent:.4f}")
        
    t_mean, t_std, t_min, t_max = calculate_stats(tech_entropies)
    h_mean, h_std, h_min, h_max = calculate_stats(hype_entropies)
    
    print("\n--- Resultados Estadísticos ---")
    print(f"Corpus Técnico: Mean = {t_mean:.4f}, StdDev = {t_std:.4f}, Min = {t_min:.4f}, Max = {t_max:.4f}")
    print(f"Corpus Hype:    Mean = {h_mean:.4f}, StdDev = {h_std:.4f}, Min = {h_min:.4f}, Max = {h_max:.4f}")
    
    # Calibrate optimal thresholds (mean +/- 3*stddev bounded)
    calibrated_min = round(max(1.5, t_mean - 3 * t_std), 2)
    calibrated_max = round(min(6.5, t_mean + 3 * t_std), 2)
    
    print("\n[CALIBRACIÓN FINAL] Umbrales Óptimos C5-REAL:")
    print(f"MIN_ENTROPY = {calibrated_min}")
    print(f"MAX_ENTROPY = {calibrated_max}")
    
    return calibrated_min, calibrated_max

if __name__ == "__main__":
    run_calibration()
