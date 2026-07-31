#ifndef VERIFIABLE_PRIMITIVES_H
#define VERIFIABLE_PRIMITIVES_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Thermodynamic & Mathematical Constants */
#define LANDAUER_KB 1.380649e-23   /* Boltzmann constant in J/K */
#define LANDAUER_LN2 0.69314718055994530942
#define DEFAULT_TEMP_KELVIN 300.0   /* Room temperature in Kelvin */
#define DEFAULT_INFINITESIMAL_EPS 1e-6f

/**
 * Result struct containing output metrics for all 10 Causal-Ontological Primitives.
 */
typedef struct {
    float pi_inv;        /* \Pi_{inv}: Invariance operator result */
    float pi_entr;       /* \Pi_{entr}: Entropy reduction operator result */
    float pi_zk;         /* \Pi_{zk}: ZK commitment vector primitive result */
    float pi_causal;     /* \Pi_{causal}: Causal graph weight projector result */
    float pi_ll;         /* \Pi_{LL}: Log-Likelihood accumulator result */
    float pi_st;         /* \Pi_{st}: Standard part map projection result (norm of standard part) */
    float pi_pmi;        /* \Pi_{PMI}: Pointwise Mutual Information accumulator result */
    double pi_landauer;  /* \Pi_{Landauer}: Thermodynamic energy dissipation result (Joules) */
    float pi_kl;         /* \Pi_{KL}: Kullback-Leibler divergence result */
    uint64_t pi_dedup;   /* \Pi_{dedup}: State deduplication bit-vector filter (matching element count) */
} primitive_results_t;

/* -------------------------------------------------------------------------- */
/* Individual Primitive Vectorized Functions                                 */
/* -------------------------------------------------------------------------- */

/**
 * 1. \Pi_{inv} (Invariance Operator)
 * Computes cosine-similarity style normalized inner product: \sum (A_i * B_i) / (\sqrt{\sum A_i^2} * \sqrt{\sum B_i^2} + eps)
 */
float primitive_pi_inv_neon(const float* a, const float* b, size_t len);

/**
 * 2. \Pi_{entr} (Entropy Reduction Operator)
 * Computes entropy reduction differential: \sum |A_i - B_i| * ln(1 + |A_i - B_i|)
 */
float primitive_pi_entr_neon(const float* a, const float* b, size_t len);

/**
 * 3. \Pi_{zk} (ZK Commitment Vector Primitive)
 * Computes deterministic homomorphic vector commitment digest: \sum (w1*A_i + w2*B_i + w3*A_i*B_i)
 */
float primitive_pi_zk_neon(const float* a, const float* b, size_t len);

/**
 * 4. \Pi_{causal} (Causal Graph Weight Projector)
 * Projects directed causal weight: \sum max(0, A_i*B_i - 0.01*A_i^2)
 */
float primitive_pi_causal_neon(const float* a, const float* b, size_t len);

/**
 * 5. \Pi_{LL} (Log-Likelihood Accumulator)
 * Accumulates Gaussian log-likelihood: -0.5 * \sum (A_i - B_i)^2 - 0.5 * len * ln(2*pi)
 */
float primitive_pi_ll_neon(const float* a, const float* b, size_t len);

/**
 * 6. \Pi_{st} (Standard Part Map Projection)
 * Projects standard part map st(x) dissipating infinitesimal noise \epsilon \in \mu(0).
 * If out_st is non-NULL, writes transformed standard parts into out_st buffer.
 * Returns norm of standard part \sum st(A_i)^2.
 */
float primitive_pi_st_neon(const float* a, const float* b, size_t len, float eps, float* out_st);

/**
 * 7. \Pi_{PMI} (Pointwise Mutual Information Accumulator)
 * Accumulates PMI across positive joint vector distributions: \sum ln((A_i * B_i + eps) / (mean_A * mean_B + eps))
 */
float primitive_pi_pmi_neon(const float* a, const float* b, size_t len);

/**
 * 8. \Pi_{Landauer} (Thermodynamic Energy Dissipation Calculation)
 * Calculates minimum thermodynamic energy dissipation: E_{min} = k_B * T * ln(2) * \sum |A_i - B_i|
 */
double primitive_pi_landauer_neon(const float* a, const float* b, size_t len, double temp_kelvin);

/**
 * 9. \Pi_{KL} (Kullback-Leibler Divergence Reduction)
 * Computes relative entropy KL divergence: \sum max(0, A_i) * ln((max(0, A_i) + eps) / (max(0, B_i) + eps))
 */
float primitive_pi_kl_neon(const float* a, const float* b, size_t len);

/**
 * 10. \Pi_{dedup} (State Deduplication Bit-Vector Filter)
 * Counts matching state components where |A_i - B_i| <= tol.
 */
uint64_t primitive_pi_dedup_neon(const float* a, const float* b, size_t len, float tol);

/* -------------------------------------------------------------------------- */
/* Unified Batch Execution Function                                           */
/* -------------------------------------------------------------------------- */

/**
 * Executes all 10 Causal-Ontological Primitives in a unified SIMD batch pipeline.
 */
void execute_10_primitives_neon(const float* a, const float* b, size_t len, primitive_results_t* out);

#ifdef __cplusplus
}
#endif

#endif /* VERIFIABLE_PRIMITIVES_H */
