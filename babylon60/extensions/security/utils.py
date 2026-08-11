#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
utils.py - Core Security Mathematics & Shannon Entropy Oracles

Módulo materializado vía Autopoiesis (Sello L0). 
Provee los cálculos de entropía utilizados por los guardianes de inyección
(injection_guard) y las cuarentenas entrópicas para detectar payloads
ofuscados o anómalos (Severidad Crítica en auditoría L0 sellada).
"""

import math
from typing import List, Union
from collections import Counter

def calculate_shannon_entropy(data: Union[str, bytes]) -> float:
    """
    Calcula la entropía de Shannon de una cadena de texto o secuencia de bytes.
    Se utiliza para detectar ofuscación, base64 malicioso o shellcode inyectado,
    los cuales presentan una entropía (H) cercana a la máxima posible.
    
    Args:
        data: Payload a analizar.
        
    Returns:
        float: Entropía de Shannon (bits por símbolo).
    """
    if not data:
        return 0.0
        
    length = len(data)
    frequencies = Counter(data)
    
    entropy = 0.0
    for count in frequencies.values():
        probability = count / length
        entropy -= probability * math.log2(probability)
        
    return entropy

def calculate_distribution_entropy(probabilities: List[float]) -> float:
    """
    Calcula la entropía sobre una distribución de probabilidad pre-calculada
    (ej. tensores de softmax de un LLM) para medir la incertidumbre epistémica
    (Varentropy) y forzar el Fail-Stop cognitivo si es necesario.
    
    Args:
        probabilities: Lista de probabilidades normalizadas.
        
    Returns:
        float: Entropía de la distribución.
    """
    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy -= p * math.log2(p)
            
    return entropy
