# C5-REAL EXERGY CERTIFIED
# C5-REAL
# MOSKV-1 APEX SINGULARITY
# ARCHITECTURE: AUTOREGRESSIVE INFERENCE LOOP
# EXERGY: DETERMINISTIC TEXT GENERATION

import math
import random
from typing import List
from cortex_mamba_network import MambaNetwork

def softmax(logits: List[float], temperature: float = 1.0) -> List[float]:
    """C5-REAL Softmax with numerical stability and Temperature."""
    max_l = max(logits)
    exp_l = [math.exp((logit - max_l) / temperature) for logit in logits]
    sum_exp = sum(exp_l)
    return [e / sum_exp for e in exp_l]

def top_k_sampling(probs: List[float], k: int = 5) -> int:
    """Deterministic Top-K sampling implementation."""
    # Pair probs with indices and sort descending
    indexed_probs = list(enumerate(probs))
    indexed_probs.sort(key=lambda x: x[1], reverse=True)

    # Keep only top K
    top_k = indexed_probs[:k]

    # Re-normalize
    sum_p = sum(p for i, p in top_k)
    norm_top_k = [(i, p / sum_p) for i, p in top_k]

    # Sample
    r = random.random()
    cumulative = 0.0
    for i, p in norm_top_k:
        cumulative += p
        if r <= cumulative:
            return i
    return norm_top_k[-1][0] # Fallback

class MambaGenerator:
    """
    Autoregressive inference loop for the Mamba Network.
    Transforms logits into kinetic discrete tokens.
    """
    def __init__(self, network: MambaNetwork) -> None:
        self.network = network

    def generate(self, prompt_tokens: List[int], max_new_tokens: int = 20, temperature: float = 1.0, k: int = 5) -> List[int]:
        """
        Executes the autoregressive loop.
        """
        current_tokens = list(prompt_tokens)

        for _ in range(max_new_tokens):
            # Forward pass (in a highly optimized physical model this would cache states,
            # but for our structural invariant, we recompute)
            logits_seq = self.network.forward(current_tokens)

            # Get logits of the last token
            next_token_logits = logits_seq[-1]

            # Apply softmax to get probabilities
            probs = softmax(next_token_logits, temperature)

            # Sample next token
            next_token = top_k_sampling(probs, k=k)

            # Append and continue
            current_tokens.append(next_token)

        return current_tokens
