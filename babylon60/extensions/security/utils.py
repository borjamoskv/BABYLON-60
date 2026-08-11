#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
utils.py - Core Security Mathematics, Entropy Oracles & Information Geometry

Módulo materializado y mejorado vía Autopoiesis (Sello L0). 
Provee los cálculos de entropía de Shannon, Varentropía, Divergencia KL y
análisis por ventana deslizante utilizados por la Cuádruple Barrera C5-REAL,
los injection guards y los filtros de cuarentena entrópica.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import List, Sequence, Union

EPSILON = 1e-12

__all__ = [
    "calculate_shannon_entropy",
    "calculate_distribution_entropy",
    "calculate_kl_divergence",
    "calculate_varentropy",
    "calculate_sliding_window_entropy",
]


def calculate_shannon_entropy(data: Union[str, bytes, Sequence[int]]) -> float:
    """
    Calcula la entropía de Shannon de una cadena de texto, secuencia de bytes o lista de tokens.
    Se utiliza para detectar ofuscación, payloads base64 maliciosos o shellcode.

    Args:
        data: Payload o secuencia a analizar.

    Returns:
        float: Entropía de Shannon H(X) en bits por símbolo (0.0 a 8.0 para bytes).
    """
    if not data:
        return 0.0

    length = len(data)
    frequencies = Counter(data)

    entropy = 0.0
    for count in frequencies.values():
        p = count / length
        entropy -= p * math.log2(p)

    return max(0.0, entropy)


def calculate_distribution_entropy(probabilities: Sequence[float]) -> float:
    """
    Calcula la entropía de Shannon sobre una distribución de probabilidad P (e.g. logits de un LLM).
    Incluye protección contra log(0) mediante epsilon clipping y normalización automática.

    Args:
        probabilities: Lista de probabilidades o ponderaciones.

    Returns:
        float: Entropía H(P) en bits.
    """
    if not probabilities:
        return 0.0

    total = sum(probabilities)
    if total <= 0:
        return 0.0

    entropy = 0.0
    for p_raw in probabilities:
        if p_raw > 0:
            p = p_raw / total
            entropy -= p * math.log2(max(p, EPSILON))

    return max(0.0, entropy)


def calculate_varentropy(probabilities: Sequence[float]) -> float:
    """
    Calcula la Varentropía (varianza de la sorpresa / información propia) de una distribución.
    Var[I(X)] = Sum(p_i * (log2(1/p_i) - H(P))^2).
    Permite detectar estados de alta confusión / alucinación probabilística en LLMs.

    Args:
        probabilities: Distribución de probabilidades de salida del modelo.

    Returns:
        float: Varentropía V(P).
    """
    if not probabilities:
        return 0.0

    total = sum(probabilities)
    if total <= 0:
        return 0.0

    norm_p = [p / total for p in probabilities if p > 0]
    if not norm_p:
        return 0.0

    h = sum(-p * math.log2(max(p, EPSILON)) for p in norm_p)

    varentropy = sum(
        p * ((-math.log2(max(p, EPSILON))) - h) ** 2 for p in norm_p
    )

    return max(0.0, varentropy)


def calculate_kl_divergence(
    p_dist: Sequence[float], q_dist: Sequence[float]
) -> float:
    """
    Calcula la Divergencia de Kullback-Leibler D_KL(P || Q).
    Utilizado en la Barrera Categórica L2 (Kl(D) audit) para medir la deriva semántica.

    Args:
        p_dist: Distribución de referencia (Manifiesto / Especificación).
        q_dist: Distribución observada (Inferencia del Agente).

    Returns:
        float: D_KL(P || Q) en nats/bits. Si Q[i] == 0 y P[i] > 0, devuelve inf.
    """
    if len(p_dist) != len(q_dist) or not p_dist:
        return 0.0

    sum_p = sum(p_dist)
    sum_q = sum(q_dist)

    if sum_p <= 0 or sum_q <= 0:
        return 0.0

    kl = 0.0
    for p_val, q_val in zip(p_dist, q_dist):
        if p_val > 0:
            p = p_val / sum_p
            q = max(q_val / sum_q, EPSILON)
            kl += p * math.log2(p / q)

    return max(0.0, kl)


def calculate_sliding_window_entropy(
    data: Union[str, bytes], window_size: int = 64, step: int = 16
) -> List[float]:
    """
    Calcula la entropía de Shannon a lo largo de un payload utilizando una ventana deslizante.
    Permite detectar sub-secciones comprimidas/encriptadas ocultas en archivos de texto plano.

    Args:
        data: Texto o bytes a escanear.
        window_size: Tamaño de cada fragmento (por defecto 64).
        step: Desplazamiento de la ventana.

    Returns:
        List[float]: Serie temporal de valores de entropía por ventana.
    """
    if len(data) <= window_size:
        return [calculate_shannon_entropy(data)]

    scores: List[float] = []
    for i in range(0, len(data) - window_size + 1, step):
        chunk = data[i : i + window_size]
        scores.append(calculate_shannon_entropy(chunk))

    return scores
