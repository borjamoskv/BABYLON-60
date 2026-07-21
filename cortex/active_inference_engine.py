import math
import logging
import dataclasses

from cortex.observer import dispatch_state_observer, StateVector
from cortex.neuro_chain import dispatch_neuro_chain, CognitiveChainVector
from cortex.tts_harness import dispatch_tts_harness, TTSHarnessState

logger = logging.getLogger("cortex.active_inference")


@dataclasses.dataclass(frozen=True)
class ActiveInferenceResult:
    """Representación inmutable de la energía libre variacional F = D_KL - E[ln p(O|S)]."""

    free_energy: float
    d_kl: float
    expected_log_likelihood: float

    def __iter__(self):
        return iter((self.free_energy, self.d_kl, self.expected_log_likelihood))


class UnifiedActiveInferenceEngine:
    """Motor unificado de Inferencia Activa C5-REAL (Falta de energía libre variacional F)."""

    def __init__(self) -> None:
        self.state_vector = StateVector()
        self.cognitive_chain_vector = CognitiveChainVector()
        self.tts_harness_state = TTSHarnessState()
        self.free_energy = 0.0
        self.d_kl = 0.0
        self.expected_log_likelihood = 0.0
        self.steps_count = 0

    def step(self, d: int, p: int, m: int) -> ActiveInferenceResult:
        if not (0 <= d <= 9 and 0 <= p <= 9 and 0 <= m <= 9):
            raise ValueError(f"Indices out of bounds [0-9]: got ({d}, {p}, {m})")

        dispatch_state_observer(d, p, m, self.state_vector)
        dispatch_neuro_chain(d, p, m, self.cognitive_chain_vector)
        dispatch_tts_harness(d, p, m, self.tts_harness_state)

        self.steps_count += 1

        # Vectorized calculation with NumPy fallback
        try:
            import numpy as np

            states = np.array(self.state_vector.states[:64], dtype=np.float64)
            cov_diag = np.array(
                [self.state_vector.covariance[i][i] for i in range(64)],
                dtype=np.float64,
            )
            mu_p = (
                np.array(self.cognitive_chain_vector.homeostasis_energy[:64])
                + np.array(self.cognitive_chain_vector.attention_weight[:64])
                + np.array(self.cognitive_chain_vector.action_torque[:64])
                + np.array(self.cognitive_chain_vector.language_entropy[:64])
            ) / 4.0
            tr_sigma_q = float(np.sum(cov_diag))
            mahalanobis = float(np.sum((states - mu_p) ** 2))
            det_sigma_q = float(np.prod(np.clip(cov_diag, 1e-5, 10.0)))
        except (ImportError, Exception):
            tr_sigma_q = sum(self.state_vector.covariance[i][i] for i in range(64))
            mahalanobis = 0.0
            for i in range(64):
                mu_p_i = (
                    self.cognitive_chain_vector.homeostasis_energy[i]
                    + self.cognitive_chain_vector.attention_weight[i]
                    + self.cognitive_chain_vector.action_torque[i]
                    + self.cognitive_chain_vector.language_entropy[i]
                ) / 4.0
                mahalanobis += (self.state_vector.states[i] - mu_p_i) ** 2
            det_sigma_q = 1.0
            for i in range(64):
                det_sigma_q_step = max(1e-5, self.state_vector.covariance[i][i])
                if det_sigma_q < 1e100:
                    det_sigma_q *= det_sigma_q_step

        self.d_kl = 0.5 * (
            tr_sigma_q + mahalanobis - 64.0 - math.log(max(1e-12, det_sigma_q))
        )
        if self.d_kl < 0:
            self.d_kl = 0.0

        tts_eff = sum(self.tts_harness_state.kv_cache_efficiency) / 64.0
        self.expected_log_likelihood = math.log(max(0.001, tts_eff))
        self.free_energy = self.d_kl - self.expected_log_likelihood

        res = ActiveInferenceResult(
            free_energy=self.free_energy,
            d_kl=self.d_kl,
            expected_log_likelihood=self.expected_log_likelihood,
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                f"Step {self.steps_count} -> F={res.free_energy:.4f}, D_KL={res.d_kl:.4f}, ELL={res.expected_log_likelihood:.4f}"
            )

        return res

    def __iter__(self):
        """Permite unpacking (free_energy, d_kl, expected_log_likelihood) para compatibilidad."""
        yield self.free_energy
        yield self.d_kl
        yield self.expected_log_likelihood
