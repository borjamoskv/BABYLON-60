// C5-REAL EXERGY CERTIFIED
#include <arm_neon.h>
#include <stddef.h>

// ARM NEON Accelerated Inverse Square Root with Cubic Householder FMA
// Utilizes Fused Multiply-Add (FMA) for maximum exergy hardware mapping.
void neon_rsqrt_cubic_fma_array(const float* in, float* out, size_t n) {
    size_t i = 0;

    // Constants for Householder cubic step
    float32x4_t half = vdupq_n_f32(0.5f);
    float32x4_t three_eighths = vdupq_n_f32(0.375f);
    float32x4_t one = vdupq_n_f32(1.0f);

    // Process 4 floats at a time
    for (; i + 3 < n; i += 4) {
        float32x4_t x = vld1q_f32(&in[i]);

        // Initial estimate (14-bit precision)
        float32x4_t y = vrsqrteq_f32(x);

        // Compute residual r = 1.0 - x * y^2 using FMA (vfmsq is Fused Multiply-Subtract: 1.0 - (x * (y*y)))
        // First compute y*y
        float32x4_t y2 = vmulq_f32(y, y);
        // r = 1.0 - x * y^2 (Negative multiply accumulate)
        // Note: vfmsq_f32(a, b, c) does a - b * c. So vfmsq_f32(one, x, y2)
        float32x4_t r = vfmsq_f32(one, x, y2);

        // Cubic Householder step: y_new = y + y * (r/2 + 3r^2/8)
        // Which is y_new = y + y * r * (0.5 + 0.375 * r)
        // FMA 1: poly = 0.5 + 0.375 * r
        float32x4_t poly = vfmaq_f32(half, three_eighths, r);

        // FMA 2: y_new = y + (y * r) * poly
        float32x4_t yr = vmulq_f32(y, r);
        float32x4_t y_new = vfmaq_f32(y, yr, poly);

        vst1q_f32(&out[i], y_new);
    }

    // Process remainder (scalar fallback)
    for (; i < n; ++i) {
        float x = in[i];
        union { float f; uint32_t i; } conv = { .f = x };
        conv.i = 0x5f375a86 - (conv.i >> 1); // Minimax
        float y = conv.f;
        float r = 1.0f - x * y * y;
        y = y + y * r * (0.5f + 0.375f * r); // Cubic step
        out[i] = y;
    }
}
