import math
from typing import Tuple
from cortex.state_observer import dispatch_state_observer, StateVector
from cortex.neuro_chain import dispatch_neuro_chain, CognitiveChainVector
from cortex.tts_harness import dispatch_tts_harness, TTSHarnessState

class UnifiedActiveInferenceEngine:
    def __init__(self) -> None:
        self.state_vector = StateVector()
        self.cognitive_chain_vector = CognitiveChainVector()
        self.tts_harness_state = TTSHarnessState()
        self.free_energy = 0.0
        self.d_kl = 0.0
        self.expected_log_likelihood = 0.0
        self.steps_count = 0

    def step(self, d: int, p: int, m: int) -> Tuple[float, float, float]:
        if not (0 <= d <= 9 and 0 <= p <= 9 and 0 <= m <= 9):
            raise ValueError("Indices out of bounds [0-9]")

        dispatch_state_observer(d, p, m, self.state_vector)
        dispatch_neuro_chain(d, p, m, self.cognitive_chain_vector)
        dispatch_tts_harness(d, p, m, self.tts_harness_state)

        self.steps_count += 1

        # Compute Variational Free Energy F = D_KL - E[ln p(O|S)]
        # q(S) = N(mu_q, Sigma_q) from state_vector (estimated state)
        # p(S) = N(mu_p, Sigma_p) representing target prior cognitive states
        # Sigma_p is assumed to be Identity for stabilization

        tr_sigma_q = sum(self.state_vector.covariance[i][i] for i in range(4))
        
        mu_p = [
            self.cognitive_chain_vector.homeostasis_energy,
            self.cognitive_chain_vector.attention_weight,
            self.cognitive_chain_vector.action_torque,
            self.cognitive_chain_vector.language_entropy
        ]
        
        mahalanobis = sum((self.state_vector.states[i] - mu_p[i]) ** 2 for i in range(4))
        
        # Determinant approximation of Sigma_q (diagonal product since it dominates)
        det_sigma_q = 1.0
        for i in range(4):
            det_sigma_q *= max(1e-5, self.state_vector.covariance[i][i])
            
        self.d_kl = 0.5 * (tr_sigma_q + mahalanobis - 4.0 - math.log(det_sigma_q))
        if self.d_kl < 0:
            self.d_kl = 0.0

        tts_eff = self.tts_harness_state.kv_cache_efficiency
        self.expected_log_likelihood = math.log(max(0.001, tts_eff))
        self.free_energy = self.d_kl - self.expected_log_likelihood

        return self.free_energy, self.d_kl, self.expected_log_likelihood
