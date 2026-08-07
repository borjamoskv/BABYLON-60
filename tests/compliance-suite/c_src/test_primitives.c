// C5-REAL EXERGY CERTIFIED
#include "verifiable_primitives.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <assert.h>
#include <float.h>

#define TEST_EPSILON 1e-3f
#define BENCHMARK_N 1000000
#define BENCHMARK_ITER 50

static double get_time_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

/* Reference Scalar Implementations for Verification */

static float ref_pi_inv(const float* a, const float* b, size_t len) {
    double sum_ab = 0.0, sum_a2 = 0.0, sum_b2 = 0.0;
    for (size_t i = 0; i < len; ++i) {
        sum_ab += (double)a[i] * (double)b[i];
        sum_a2 += (double)a[i] * (double)a[i];
        sum_b2 += (double)b[i] * (double)b[i];
    }
    double denom = sqrt(sum_a2) * sqrt(sum_b2) + 1e-12;
    return (float)(sum_ab / denom);
}

static float ref_pi_entr(const float* a, const float* b, size_t len) {
    double sum = 0.0;
    for (size_t i = 0; i < len; ++i) {
        double diff = fabs((double)a[i] - (double)b[i]);
        sum += diff * log1p(diff);
    }
    return (float)sum;
}

static float ref_pi_zk(const float* a, const float* b, size_t len) {
    double sum = 0.0;
    for (size_t i = 0; i < len; ++i) {
        double va = (double)a[i];
        double vb = (double)b[i];
        sum += (0.6180339887 * va + 1.4142135623 * vb + 2.7182818284 * va * vb);
    }
    return (float)sum;
}

static float ref_pi_causal(const float* a, const float* b, size_t len) {
    double sum = 0.0;
    for (size_t i = 0; i < len; ++i) {
        double va = (double)a[i];
        double vb = (double)b[i];
        double val = va * vb - 0.01 * va * va;
        if (val > 0.0) sum += val;
    }
    return (float)sum;
}

static float ref_pi_ll(const float* a, const float* b, size_t len) {
    double sum_diff2 = 0.0;
    for (size_t i = 0; i < len; ++i) {
        double diff = (double)a[i] - (double)b[i];
        sum_diff2 += diff * diff;
    }
    const double ln_2pi = 1.8378770664093455;
    return (float)(-0.5 * sum_diff2 - 0.5 * (double)len * ln_2pi);
}

static float ref_pi_st(const float* a, size_t len, float eps) {
    double sum_st2 = 0.0;
    for (size_t i = 0; i < len; ++i) {
        double val = (fabs((double)a[i]) >= (double)eps) ? (double)a[i] : 0.0;
        sum_st2 += val * val;
    }
    return (float)sum_st2;
}

static float ref_pi_pmi(const float* a, const float* b, size_t len) {
    double sum_a = 0.0, sum_b = 0.0;
    for (size_t i = 0; i < len; ++i) {
        sum_a += (double)a[i];
        sum_b += (double)b[i];
    }
    double mean_a = sum_a / (double)len;
    double mean_b = sum_b / (double)len;
    double denom = mean_a * mean_b + 1e-12;

    double sum_pmi = 0.0;
    for (size_t i = 0; i < len; ++i) {
        if (a[i] > 0.0f && b[i] > 0.0f) {
            double ratio = ((double)a[i] * (double)b[i] + 1e-12) / denom;
            sum_pmi += log(ratio);
        }
    }
    return (float)sum_pmi;
}

static double ref_pi_landauer(const float* a, const float* b, size_t len, double temp_kelvin) {
    double sum_diff = 0.0;
    for (size_t i = 0; i < len; ++i) {
        sum_diff += fabs((double)a[i] - (double)b[i]);
    }
    double energy_per_bit = LANDAUER_KB * temp_kelvin * LANDAUER_LN2;
    return sum_diff * energy_per_bit;
}

static float ref_pi_kl(const float* a, const float* b, size_t len) {
    double sum_kl = 0.0;
    for (size_t i = 0; i < len; ++i) {
        double va = (a[i] > 0.0f) ? (double)a[i] : 0.0;
        double vb = (b[i] > 0.0f) ? (double)b[i] : 0.0;
        double ratio = (va + 1e-9) / (vb + 1e-9);
        sum_kl += va * log(ratio);
    }
    return (float)sum_kl;
}

static uint64_t ref_pi_dedup(const float* a, const float* b, size_t len, float tol) {
    uint64_t count = 0;
    for (size_t i = 0; i < len; ++i) {
        if (fabsf(a[i] - b[i]) <= tol) {
            count++;
        }
    }
    return count;
}

/* Test Functions */

static void test_correctness_and_tails(void) {
    printf("--- [TEST 1] Correctness & Variable Tail Alignment ---\n");
    size_t test_lengths[] = {1, 2, 3, 4, 5, 7, 13, 16, 127, 1024, 9999};
    size_t num_tests = sizeof(test_lengths) / sizeof(test_lengths[0]);

    for (size_t idx = 0; idx < num_tests; ++idx) {
        size_t len = test_lengths[idx];
        float* a = (float*)malloc(len * sizeof(float));
        float* b = (float*)malloc(len * sizeof(float));

        for (size_t i = 0; i < len; ++i) {
            a[i] = (float)(i % 100) * 0.05f + 0.1f;
            b[i] = (float)(i % 75) * 0.04f + 0.08f;
        }

        primitive_results_t res;
        execute_10_primitives_neon(a, b, len, &res);

        float r_inv = ref_pi_inv(a, b, len);
        float r_entr = ref_pi_entr(a, b, len);
        float r_zk = ref_pi_zk(a, b, len);
        float r_causal = ref_pi_causal(a, b, len);
        float r_ll = ref_pi_ll(a, b, len);
        float r_st = ref_pi_st(a, len, DEFAULT_INFINITESIMAL_EPS);
        float r_pmi = ref_pi_pmi(a, b, len);
        double r_landauer = ref_pi_landauer(a, b, len, DEFAULT_TEMP_KELVIN);
        float r_kl = ref_pi_kl(a, b, len);
        uint64_t r_dedup = ref_pi_dedup(a, b, len, 1e-4f);

        assert(fabsf(res.pi_inv - r_inv) < 1e-2f * (fabsf(r_inv) + 1.0f));
        assert(fabsf(res.pi_entr - r_entr) < 1e-2f * (fabsf(r_entr) + 1.0f));
        assert(fabsf(res.pi_zk - r_zk) < 1e-2f * (fabsf(r_zk) + 1.0f));
        assert(fabsf(res.pi_causal - r_causal) < 1e-2f * (fabsf(r_causal) + 1.0f));
        assert(fabsf(res.pi_ll - r_ll) < 1e-2f * (fabsf(r_ll) + 1.0f));
        assert(fabsf(res.pi_st - r_st) < 1e-2f * (fabsf(r_st) + 1.0f));
        assert(fabsf(res.pi_pmi - r_pmi) < 1e-2f * (fabsf(r_pmi) + 1.0f));
        assert(fabs(res.pi_landauer - r_landauer) < 1e-2 * (fabs(r_landauer) + 1e-25));
        assert(fabsf(res.pi_kl - r_kl) < 1e-2f * (fabsf(r_kl) + 1.0f));
        assert(res.pi_dedup == r_dedup);

        free(a);
        free(b);
    }
    printf("[PASS] All 10 primitives match reference implementations across all tail sizes!\n\n");
}

static void test_edge_cases(void) {
    printf("--- [TEST 2] Edge Cases: Denormals, Zeros & Thermodynamic Bounds ---\n");

    size_t len = 1000;
    float* a = (float*)calloc(len, sizeof(float));
    float* b = (float*)calloc(len, sizeof(float));

    /* Case A: Absolute Zeros */
    primitive_results_t res_zero;
    execute_10_primitives_neon(a, b, len, &res_zero);
    assert(res_zero.pi_landauer == 0.0);
    assert(res_zero.pi_dedup == (uint64_t)len);
    assert(!isnan(res_zero.pi_inv) && !isinf(res_zero.pi_inv));
    assert(!isnan(res_zero.pi_pmi) && !isinf(res_zero.pi_pmi));
    assert(!isnan(res_zero.pi_kl) && !isinf(res_zero.pi_kl));

    /* Case B: Subnormals & Denormals */
    for (size_t i = 0; i < len; ++i) {
        a[i] = 1e-38f;
        b[i] = 1e-39f;
    }
    primitive_results_t res_denorm;
    execute_10_primitives_neon(a, b, len, &res_denorm);
    assert(!isnan(res_denorm.pi_inv));
    assert(!isnan(res_denorm.pi_entr));
    assert(!isnan(res_denorm.pi_landauer));
    assert(res_denorm.pi_st == 0.0f); /* \Pi_{st} purges subnormals below 1e-6 */

    /* Case C: Thermodynamic Landauer Temperature Limits */
    double energy_0k = primitive_pi_landauer_neon(a, b, len, 0.0);
    assert(energy_0k == 0.0);

    double energy_300k = primitive_pi_landauer_neon(a, b, len, 300.0);
    double energy_1000k = primitive_pi_landauer_neon(a, b, len, 1000.0);
    assert(energy_300k > 0.0);
    assert(energy_1000k > energy_300k);

    /* Case D: Standard Part Projection Array Output */
    float out_st[10];
    float in_a[10] = {1.0f, 1e-7f, -0.5f, 5e-8f, 2.5f, 0.0f, 1e-5f, -1e-6f, 0.1f, 1e-10f};
    primitive_pi_st_neon(in_a, in_a, 10, 1e-6f, out_st);
    assert(out_st[0] == 1.0f);
    assert(out_st[1] == 0.0f); /* 1e-7 dissipated */
    assert(out_st[2] == -0.5f);
    assert(out_st[3] == 0.0f); /* 5e-8 dissipated */
    assert(out_st[4] == 2.5f);

    free(a);
    free(b);
    printf("[PASS] Edge cases, subnormals, Landauer physical bounds, and standard part map verified!\n\n");
}

static void benchmark_performance(void) {
    printf("--- [TEST 3] ARM64 NEON SIMD Accelerator Throughput Benchmark ---\n");
    printf("Dataset size: %'d vectors (Float32 x 2) across %d iterations\n", BENCHMARK_N, BENCHMARK_ITER);

    float* a = (float*)malloc(BENCHMARK_N * sizeof(float));
    float* b = (float*)malloc(BENCHMARK_N * sizeof(float));

    for (int i = 0; i < BENCHMARK_N; ++i) {
        a[i] = (float)(i % 256) * 0.01f + 0.05f;
        b[i] = (float)(i % 128) * 0.02f + 0.01f;
    }

    primitive_results_t res;

    /* Warmup */
    execute_10_primitives_neon(a, b, BENCHMARK_N, &res);

    double t0 = get_time_sec();
    for (int iter = 0; iter < BENCHMARK_ITER; ++iter) {
        execute_10_primitives_neon(a, b, BENCHMARK_N, &res);
    }
    double t1 = get_time_sec();

    double total_time = t1 - t0;
    double avg_time_per_run = total_time / BENCHMARK_ITER;
    double total_ops = (double)BENCHMARK_N * (double)BENCHMARK_ITER * 10.0; /* 10 primitives */
    double mops = (total_ops / total_time) / 1e6;
    double gb_processed = ((double)BENCHMARK_N * sizeof(float) * 2.0 * BENCHMARK_ITER) / 1e9;
    double bandwidth_gbs = gb_processed / total_time;

    printf("\n=================================================================\n");
    printf(" BRUTALIST BENCHMARK RESULTS (ARM64 NEON Apple Silicon)\n");
    printf("=================================================================\n");
    printf(" Total Time (50 runs):     %.4f s\n", total_time);
    printf(" Latency per 1M batch:     %.3f ms\n", avg_time_per_run * 1000.0);
    printf(" Primitive Throughput:     %.2f Million Primitive Ops / sec\n", mops);
    printf(" Effective Memory BW:      %.2f GB/s\n", bandwidth_gbs);
    printf("=================================================================\n");
    printf(" Sample Results:\n");
    printf("   \u03A0_inv:      %.6f\n", res.pi_inv);
    printf("   \u03A0_entr:     %.6f\n", res.pi_entr);
    printf("   \u03A0_zk:       %.6f\n", res.pi_zk);
    printf("   \u03A0_causal:   %.6f\n", res.pi_causal);
    printf("   \u03A0_LL:       %.6f\n", res.pi_ll);
    printf("   \u03A0_st:       %.6f\n", res.pi_st);
    printf("   \u03A0_PMI:      %.6f\n", res.pi_pmi);
    printf("   \u03A0_Landauer: %.6e Joules\n", res.pi_landauer);
    printf("   \u03A0_KL:       %.6f\n", res.pi_kl);
    printf("   \u03A0_dedup:    %llu matches\n", (unsigned long long)res.pi_dedup);
    printf("=================================================================\n\n");

    free(a);
    free(b);
}

int main(void) {
    printf("\n=================================================================\n");
    printf(" AUTODIDACT-\u03A9 Milestone 1: NEON SIMD Accelerator Test Harness\n");
    printf("=================================================================\n\n");

    test_correctness_and_tails();
    test_edge_cases();
    benchmark_performance();

    printf("\u2705 ALL TESTS PASSED SUCCESSFULLY WITH 100%% VERIFICATION!\n\n");
    return 0;
}
