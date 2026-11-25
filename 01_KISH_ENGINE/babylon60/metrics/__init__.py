"""Mathematical scalability evaluators (Gunther USL, Amdahl, Gustafson, Kingman VUT, and C5 log-elasticities)."""

from .scalability_usl import (
    USLFitResult,
    amdahl_speedup,
    chinchilla_loss,
    composite_j_elasticity,
    discrete_log_elasticity,
    fit_usl_parameters,
    gustafson_speedup,
    kingman_waiting_time,
    littles_law_concurrency,
    usl_capacity,
    usl_peak_concurrency,
)

__all__ = [
    "USLFitResult",
    "amdahl_speedup",
    "chinchilla_loss",
    "composite_j_elasticity",
    "discrete_log_elasticity",
    "fit_usl_parameters",
    "gustafson_speedup",
    "kingman_waiting_time",
    "littles_law_concurrency",
    "usl_capacity",
    "usl_peak_concurrency",
]
