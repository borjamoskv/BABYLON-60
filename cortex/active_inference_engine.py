import math
from typing import Tuple
from cortex.state_observer import dispatch_state_observer, StateVector
from cortex.neuro_chain import dispatch_neuro_chain, CognitiveChainVector
from cortex.tts_harness import dispatch_tts_harness, TTSHarnessState

class UnifiedActiveInferenceEngine:
    def __init__(self):
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

        obs_norm = self.state_vector.norm_error
        neuro_norm = self.cognitive_chain_vector.prediction_error
        tts_eff = self.tts_harness_state.kv_cache_efficiency

        self.d_kl = abs(obs_norm - neuro_norm)
        self.expected_log_likelihood = math.log(max(0.001, tts_eff))
        self.free_energy = self.d_kl - self.expected_log_likelihood

        return self.free_energy, self.d_kl, self.expected_log_likelihood
