#!/usr/bin/env python3
"""
audit_kl_d.py — Utility script for categorical hallucination audits in Kl(D).

Calculates:
1. Pointwise Left Kan Extension Lan_i(i*X) in Kl(D) given a stochastic transition matrix T,
   prior distribution pi0, and context window P ⊆ H.
2. Quantitative Hallucination Rate H(t | P) = 1 - P_Lan(S_t* | P).
3. Surprisal / Counit Defect D_counidad(t | P) = -log2(P_Lan(S_t* | P)).
4. Wasserstein-1 distance metric and epsilon-coverage for T3 stochastic state space bound.
"""

import sys
import json
import numpy as np


def compute_kan_extension_kl_d(S, T, pi0, history, window, target_t):
    """
    Computes Lan_i(i*X)(target_t) in Kl(D).
\x20\x20\x20\x20
    S: list of state names
    T: stochastic transition matrix (n x n)
    pi0: prior distribution vector (n)
    history: dict {t: state_name}
    window: list of timesteps observed P
    target_t: timestep to evaluate
    """
    n = len(S)
    T = np.array(T, dtype=float)
    pi0 = np.array(pi0, dtype=float)

    # Normalize
    T = T / T.sum(axis=1, keepdims=True)
    pi0 = pi0 / pi0.sum()

    P = sorted(window)

    if target_t in P:
        idx = S.index(history[target_t])
        dist = np.zeros(n)
        dist[idx] = 1.0
        return dist

    if target_t < min(P):
        p1 = P[0]
        s_p1_idx = S.index(history[p1])
        steps = p1 - target_t
        T_steps = np.linalg.matrix_power(T, steps)
        joint = pi0 * T_steps[:, s_p1_idx]
        return joint / joint.sum() if joint.sum() > 0 else np.ones(n) / n

    if target_t > max(P):
        p_last = max(P)
        s_plast_idx = S.index(history[p_last])
        steps = target_t - p_last
        T_steps = np.linalg.matrix_power(T, steps)
        return T_steps[s_plast_idx, :]

    # Internal gap
    p_prev = max([p for p in P if p < target_t])
    p_next = min([p for p in P if p > target_t])
    s_prev_idx = S.index(history[p_prev])
    s_next_idx = S.index(history[p_next])

    T_fwd = np.linalg.matrix_power(T, target_t - p_prev)
    T_bwd = np.linalg.matrix_power(T, p_next - target_t)

    joint = T_fwd[s_prev_idx, :] * T_bwd[:, s_next_idx]
    return joint / joint.sum() if joint.sum() > 0 else np.ones(n) / n


def compute_wasserstein_1d(p, q):
    """Computes 1D Wasserstein distance (L1 norm of cumulative distributions)."""
    return np.sum(np.abs(np.cumsum(p) - np.cumsum(q)))


def audit_system(S, T, pi0, history, window, target_timesteps):
    results = []
    for t in target_timesteps:
        dist = compute_kan_extension_kl_d(S, T, pi0, history, window, t)
        true_state = history[t]
        true_idx = S.index(true_state)
        p_true = float(dist[true_idx])
        hallucination_rate = 1.0 - p_true
        surprisal = float(-np.log2(p_true)) if p_true > 1e-12 else 100.0

        # Dirac delta on truth
        dirac = np.zeros(len(S))
        dirac[true_idx] = 1.0
        w1 = float(compute_wasserstein_1d(dist, dirac))

        results.append({
            "target_t": int(t),
            "true_state": true_state,
            "p_true": round(p_true, 4),
            "hallucination_rate": round(hallucination_rate, 4),
            "surprisal_bits": round(surprisal, 4),
            "wasserstein_dist": round(w1, 4),
            "distribution": {S[i]: round(float(dist[i]), 4) for i in range(len(S))}
        })
    return results


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        # Example JSON invocation
        data = json.load(sys.stdin)
        res = audit_system(data["states"], data["T"], data["pi0"],
                           {int(k): v for k, v in data["history"].items()},
                           data["window"], data["targets"])
        print(json.dumps(res, indent=2))
    else:
        print("Categorical Hallucination Audit CLI Script (audit_kl_d.py)")
        print("Usage: python3 audit_kl_d.py --json < input.json")


if __name__ == "__main__":
    main()
