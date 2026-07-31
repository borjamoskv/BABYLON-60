#include <arm_neon.h>
#include <dispatch/dispatch.h>
#include <stddef.h>
#include <stdint.h>

// C5-REAL EXERGY CERTIFIED
// Fast-Softmax Engine: SIMD NEON + GCD TLP + FMA Fast-Exp
// Axioms Ω21, Ω23, Ω26

// Extremely fast exp(x) approximation via IEEE-754 bit trick using FMA
static inline float32x4_t fast_exp_neon(float32x4_t x) {
    // Fused Multiply-Add (Axiom Ω26): x * 12102203.0 + 1064866805.0
    float32x4_t res = vmlaq_f32(vdupq_n_f32(1064866805.0f), x, vdupq_n_f32(12102203.0f));
    int32x4_t bits = vcvtq_s32_f32(res); // Convert to integer

    // Bounds check to avoid NaN/garbage for very small inputs
    uint32x4_t mask = vcgeq_f32(x, vdupq_n_f32(-87.3f));
    int32x4_t bounded = vbslq_s32(mask, bits, vdupq_n_s32(0));

    return vreinterpretq_f32_s32(bounded);
}

// Fast Reciprocal via Newton-Raphson iteration
static inline float32x4_t fast_reciprocal_neon(float32x4_t x) {
    float32x4_t recpe = vrecpeq_f32(x);
    float32x4_t recps = vrecpsq_f32(recpe, x);
    return vmulq_f32(recpe, recps);
}

// Exposed FFI Function
// Applies Softmax independently over each row.
void fast_softmax_neon(float *__restrict__ data, size_t rows, size_t cols) {
    // Thread-Level Parallelism via GCD (Axiom Ω23)
    dispatch_apply(rows, dispatch_get_global_queue(QOS_CLASS_USER_INTERACTIVE, 0), ^(size_t r) {
        float *row = data + r * cols;
        size_t c = 0;

        // ----------------------------------------------------
        // PHASE 1: Find Row Max (ILP 4x Unrolled - Axiom Ω21)
        // ----------------------------------------------------
        float32x4_t max0 = vdupq_n_f32(-1e30f);
        float32x4_t max1 = vdupq_n_f32(-1e30f);
        float32x4_t max2 = vdupq_n_f32(-1e30f);
        float32x4_t max3 = vdupq_n_f32(-1e30f);

        for (c = 0; c + 15 < cols; c += 16) {
            float32x4_t v0 = vld1q_f32(row + c);
            float32x4_t v1 = vld1q_f32(row + c + 4);
            float32x4_t v2 = vld1q_f32(row + c + 8);
            float32x4_t v3 = vld1q_f32(row + c + 12);

            max0 = vmaxq_f32(max0, v0);
            max1 = vmaxq_f32(max1, v1);
            max2 = vmaxq_f32(max2, v2);
            max3 = vmaxq_f32(max3, v3);
        }

        max0 = vmaxq_f32(max0, max1);
        max2 = vmaxq_f32(max2, max3);
        max0 = vmaxq_f32(max0, max2);

        float max_val = vmaxvq_f32(max0);

        // Scalar tail for max
        for (; c < cols; c++) {
            if (row[c] > max_val) max_val = row[c];
        }

        // ----------------------------------------------------
        // PHASE 2: Subtract Max, Fast Exp, and Sum (ILP 4x)
        // ----------------------------------------------------
        float32x4_t vmax_splat = vdupq_n_f32(max_val);
        float32x4_t sum0 = vdupq_n_f32(0.0f);
        float32x4_t sum1 = vdupq_n_f32(0.0f);
        float32x4_t sum2 = vdupq_n_f32(0.0f);
        float32x4_t sum3 = vdupq_n_f32(0.0f);

        for (c = 0; c + 15 < cols; c += 16) {
            float32x4_t v0 = vld1q_f32(row + c);
            float32x4_t v1 = vld1q_f32(row + c + 4);
            float32x4_t v2 = vld1q_f32(row + c + 8);
            float32x4_t v3 = vld1q_f32(row + c + 12);

            v0 = vsubq_f32(v0, vmax_splat);
            v1 = vsubq_f32(v1, vmax_splat);
            v2 = vsubq_f32(v2, vmax_splat);
            v3 = vsubq_f32(v3, vmax_splat);

            v0 = fast_exp_neon(v0);
            v1 = fast_exp_neon(v1);
            v2 = fast_exp_neon(v2);
            v3 = fast_exp_neon(v3);

            vst1q_f32(row + c, v0);
            vst1q_f32(row + c + 4, v1);
            vst1q_f32(row + c + 8, v2);
            vst1q_f32(row + c + 12, v3);

            sum0 = vaddq_f32(sum0, v0);
            sum1 = vaddq_f32(sum1, v1);
            sum2 = vaddq_f32(sum2, v2);
            sum3 = vaddq_f32(sum3, v3);
        }

        sum0 = vaddq_f32(sum0, sum1);
        sum2 = vaddq_f32(sum2, sum3);
        sum0 = vaddq_f32(sum0, sum2);

        float total_sum = vaddvq_f32(sum0);

        // Scalar tail for exp and sum
        // A simple scalar exp is enough for tail, or we could just use libc expf here since it's < 15 elements
        for (; c < cols; c++) {
            float e = row[c] - max_val;
            // Hacky scalar fast exp for consistency
            union { float f; int32_t i; } val;
            val.f = e * 12102203.0f + 1064866805.0f;
            if (e < -87.3f) val.i = 0;
            row[c] = val.f;
            total_sum += row[c];
        }

        // ----------------------------------------------------
        // PHASE 3: Normalize using Newton-Raphson Reciprocal
        // ----------------------------------------------------
        float32x4_t vsum_recip = fast_reciprocal_neon(vdupq_n_f32(total_sum));

        for (c = 0; c + 15 < cols; c += 16) {
            float32x4_t v0 = vld1q_f32(row + c);
            float32x4_t v1 = vld1q_f32(row + c + 4);
            float32x4_t v2 = vld1q_f32(row + c + 8);
            float32x4_t v3 = vld1q_f32(row + c + 12);

            v0 = vmulq_f32(v0, vsum_recip);
            v1 = vmulq_f32(v1, vsum_recip);
            v2 = vmulq_f32(v2, vsum_recip);
            v3 = vmulq_f32(v3, vsum_recip);

            vst1q_f32(row + c, v0);
            vst1q_f32(row + c + 4, v1);
            vst1q_f32(row + c + 8, v2);
            vst1q_f32(row + c + 12, v3);
        }

        // Scalar tail
        float scalar_recip = 1.0f / total_sum; // Safe enough, just 1 div per row
        for (; c < cols; c++) {
            row[c] *= scalar_recip;
        }
    });
}
