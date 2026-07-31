// C5-REAL EXERGY CERTIFIED
#include <arm_neon.h>
#include <stddef.h>

// ARM NEON Accelerated Inverse Square Root
// Computes 4 float32 values simultaneously using native silicon estimation and step.
void neon_rsqrt_f32_array(const float* in, float* out, size_t n) {
    size_t i = 0;

    // Process 4 floats at a time
    for (; i + 3 < n; i += 4) {
        float32x4_t vec_in = vld1q_f32(&in[i]);

        // Native ARM NEON Reciprocal Square Root Estimate (14-bit precision)
        float32x4_t vec_est = vrsqrteq_f32(vec_in);

        // Native ARM NEON Reciprocal Square Root Step (Newton-Raphson iteration in hardware)
        // This computes: est * (1.5 - 0.5 * in * est * est)
        float32x4_t vec_step = vrsqrtsq_f32(vec_in, vmulq_f32(vec_est, vec_est));
        float32x4_t vec_out = vmulq_f32(vec_est, vec_step);

        // Optional second step for maximum precision (~24-bit)
        vec_step = vrsqrtsq_f32(vec_in, vmulq_f32(vec_out, vec_out));
        vec_out = vmulq_f32(vec_out, vec_step);

        vst1q_f32(&out[i], vec_out);
    }

    // Process remainder
    for (; i < n; ++i) {
        // Fallback for remainder: Carmack/Walczyk minimax 0x5f375a86
        float x = in[i];
        float x2 = x * 0.5f;
        union { float f; uint32_t i; } conv = { .f = x };
        conv.i = 0x5f375a86 - (conv.i >> 1);
        conv.f = conv.f * (1.5f - (x2 * conv.f * conv.f));
        conv.f = conv.f * (1.5f - (x2 * conv.f * conv.f)); // 2nd iter
        out[i] = conv.f;
    }
}
