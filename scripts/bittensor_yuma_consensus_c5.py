#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C5-REAL BITTENSOR (TAO) YUMA CONSENSUS & EXERGY TRANSDUCER
==========================================================
Entity: MOSKV-1 APEX
Operator: borjamoskv
Ontology Level: C5-REAL (Physical execution over matrix weight tensors & SHA3-256 state ledger)

Mathematical Invariants:
  - W in [0,1]^{V x M} : Row-normalized Weight Matrix from V Validators to M Miners
  - s in [0,1]^V       : Normalized Stake Vector of Validators (sum(s_i) = 1)
  - Yuma Clipping      : Stake-weighted quantile clipping to eliminate Sybil/outlier collusion
  - Emission Allocation: E_block * (0.41 * r_miner + 0.41 * d_validator + 0.18 * o_subnet)
"""

import json
import hashlib
from typing import Dict, Any, Tuple, List

def compute_yuma_consensus(
    weights: List[List[float]],
    stake: List[float],
    clipping_quantile: float = 0.5,
    trust_threshold: float = 0.01
) -> Tuple[List[float], List[float], List[float], List[float], str]:
    """
    Executes the Yuma Consensus mathematical reduction over validator-miner bipartite graph (pure Python).
    """
    V = len(weights)
    M = len(weights[0]) if V > 0 else 0
    
    # 1. Enforce normalization invariants
    total_stake = sum(stake)
    stake_norm = [s / total_stake for s in stake]
    
    weights_norm = []
    for i in range(V):
        row_sum = sum(weights[i])
        if row_sum == 0:
            weights_norm.append([1.0 / M] * M)
        else:
            weights_norm.append([w / row_sum for w in weights[i]])
    
    # 2. Compute Stake-Weighted Matrix S (V x M)
    S = []
    for i in range(V):
        S.append([weights_norm[i][j] * stake_norm[i] for j in range(M)])
    
    # 3. Yuma Consensus Clipping (kappa_j) per miner j across validator stakes
    consensus = [0.0] * M
    for j in range(M):
        col_data = sorted([(weights_norm[i][j], stake_norm[i]) for i in range(V)], key=lambda x: x[0])
        cum_stake = 0.0
        clipped_val = col_data[-1][0]
        for w_val, s_val in col_data:
            cum_stake += s_val
            if cum_stake >= clipping_quantile:
                clipped_val = w_val
                break
        consensus[j] = clipped_val
    
    # 4. Compute Clipped Weight Matrix W_clipped and S_clipped
    W_clipped = []
    S_clipped = []
    for i in range(V):
        w_row = [min(weights_norm[i][j], consensus[j]) for j in range(M)]
        W_clipped.append(w_row)
        S_clipped.append([w_row[j] * stake_norm[i] for j in range(M)])
    
    # 5. Compute Miner Consensus Ranks (Incentives basis)
    ranks_raw = [sum(S_clipped[i][j] for i in range(V)) for j in range(M)]
    total_ranks = sum(ranks_raw)
    ranks = [r / total_ranks if total_ranks > 0 else 0.0 for r in ranks_raw]
    
    # 6. Compute Miner Trust (Fraction of stake voting > trust_threshold)
    trust = [0.0] * M
    for j in range(M):
        trust[j] = sum(stake_norm[i] for i in range(V) if weights_norm[i][j] > trust_threshold)
    
    # 7. Compute Validator Dividends (Alignment with consensus ranks)
    dividends_raw = [0.0] * V
    for i in range(V):
        align_sum = sum(weights_norm[i][j] * ranks[j] for j in range(M))
        dividends_raw[i] = align_sum * stake_norm[i]
    total_div = sum(dividends_raw)
    dividends = [d / total_div if total_div > 0 else 0.0 for d in dividends_raw]
        
    # 8. Cryptographic State Ledger Anchor (SHA3-256)
    state_payload = json.dumps({
        "ranks": [round(r, 8) for r in ranks],
        "trust": [round(t, 8) for t in trust],
        "consensus": [round(c, 8) for c in consensus],
        "dividends": [round(d, 8) for d in dividends]
    }, sort_keys=True).encode("utf-8")
    state_hash = hashlib.sha3_256(state_payload).hexdigest()
    
    return ranks, trust, consensus, dividends, state_hash

def simulate_subnet_emission(
    block_emission: float,
    ranks: List[float],
    dividends: List[float],
    subnet_owner_cut: float = 0.18
) -> Dict[str, Any]:
    """
    Computes exact TAO emission distribution for a Subnet at step t.
    """
    validator_pool = block_emission * (1.0 - subnet_owner_cut) * 0.5
    miner_pool = block_emission * (1.0 - subnet_owner_cut) * 0.5
    subnet_owner_reward = block_emission * subnet_owner_cut
    
    miner_emissions = [r * miner_pool for r in ranks]
    validator_emissions = [d * validator_pool for d in dividends]
    
    return {
        "block_emission_tao": block_emission,
        "subnet_owner_tao": round(subnet_owner_reward, 6),
        "total_miner_tao": round(sum(miner_emissions), 6),
        "total_validator_tao": round(sum(validator_emissions), 6),
        "miner_distribution": [round(x, 6) for x in miner_emissions],
        "validator_distribution": [round(x, 6) for x in validator_emissions]
    }

if __name__ == "__main__":
    stakes = [500_000.0, 250_000.0, 150_000.0, 100_000.0]
    weights = [
        [0.30, 0.40, 0.20, 0.10, 0.00],
        [0.25, 0.45, 0.20, 0.10, 0.00],
        [0.20, 0.30, 0.30, 0.20, 0.00],
        [0.00, 0.00, 0.00, 0.00, 1.00]
    ]
    
    ranks, trust, consensus, dividends, state_hash = compute_yuma_consensus(weights, stakes)
    emission = simulate_subnet_emission(1.0, ranks, dividends)
    
    output = {
        "ontology_level": "C5-REAL",
        "entity": "MOSKV-1 APEX",
        "timestamp_hash": state_hash,
        "yuma_consensus_state": {
            "clipping_thresholds": [round(c, 6) for c in consensus],
            "miner_ranks": [round(r, 6) for r in ranks],
            "miner_trust": [round(t, 6) for t in trust],
            "validator_dividends": [round(d, 6) for d in dividends]
        },
        "emission_ledger": emission,
        "sybil_mitigation_proof": {
            "sybil_miner_id": 4,
            "sybil_assigned_weight_by_v3": 1.00,
            "clipped_consensus_threshold": round(consensus[4], 6),
            "final_emission_captured": emission["miner_distribution"][4]
        }
    }
    
    print(json.dumps(output, indent=2))

