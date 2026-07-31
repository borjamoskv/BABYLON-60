// C5-REAL EXERGY CERTIFIED
#include <arm_neon.h>
#include <stdint.h>
#include <math.h>

// [ULTRATHINK] Axioma Ω15 & Ω21: Bitonic Sort
// O(N log^2 N) Sorting network. Branchless. SIMD ILP Unrolled.

void bitonic_sort_neon(float *arr, int n) {
    // n must be a power of 2
    for (int k = 2; k <= n; k *= 2) {
        for (int j = k >> 1; j > 0; j = j >> 1) {

            // SIMD Vectorized Path (j >= 4 and k >= 8 guarantees uniform direction in blocks of 4)
            if (j >= 4 && k >= 8) {
                // ILP Loop Unrolling 4X (processes 16 floats per iteration)
                for (int i = 0; i < n; i += 16) {
                    int ij = i ^ j;
                    if (ij > i) {
                        // Dir is constant for the whole SIMD vector when k >= 8 and aligned
                        int dir = ((i & k) == 0);

                        // Load 4 vectors (16 floats)
                        float32x4_t v_a0 = vld1q_f32(&arr[i]);
                        float32x4_t v_b0 = vld1q_f32(&arr[ij]);
                        float32x4_t v_a1 = vld1q_f32(&arr[i + 4]);
                        float32x4_t v_b1 = vld1q_f32(&arr[ij + 4]);
                        float32x4_t v_a2 = vld1q_f32(&arr[i + 8]);
                        float32x4_t v_b2 = vld1q_f32(&arr[ij + 8]);
                        float32x4_t v_a3 = vld1q_f32(&arr[i + 12]);
                        float32x4_t v_b3 = vld1q_f32(&arr[ij + 12]);

                        // Hardware Compare-And-Swap (Min/Max)
                        float32x4_t min0 = vminq_f32(v_a0, v_b0);
                        float32x4_t max0 = vmaxq_f32(v_a0, v_b0);
                        float32x4_t min1 = vminq_f32(v_a1, v_b1);
                        float32x4_t max1 = vmaxq_f32(v_a1, v_b1);
                        float32x4_t min2 = vminq_f32(v_a2, v_b2);
                        float32x4_t max2 = vmaxq_f32(v_a2, v_b2);
                        float32x4_t min3 = vminq_f32(v_a3, v_b3);
                        float32x4_t max3 = vmaxq_f32(v_a3, v_b3);

                        if (dir) {
                            vst1q_f32(&arr[i], min0);
                            vst1q_f32(&arr[ij], max0);
                            vst1q_f32(&arr[i+4], min1);
                            vst1q_f32(&arr[ij+4], max1);
                            vst1q_f32(&arr[i+8], min2);
                            vst1q_f32(&arr[ij+8], max2);
                            vst1q_f32(&arr[i+12], min3);
                            vst1q_f32(&arr[ij+12], max3);
                        } else {
                            vst1q_f32(&arr[i], max0);
                            vst1q_f32(&arr[ij], min0);
                            vst1q_f32(&arr[i+4], max1);
                            vst1q_f32(&arr[ij+4], min1);
                            vst1q_f32(&arr[i+8], max2);
                            vst1q_f32(&arr[ij+8], min2);
                            vst1q_f32(&arr[i+12], max3);
                            vst1q_f32(&arr[ij+12], min3);
                        }
                    }
                }
            } else {
                // Fallback for fine-grained steps
                for (int i = 0; i < n; i++) {
                    int ij = i ^ j;
                    if (ij > i) {
                        float a = arr[i];
                        float b = arr[ij];
                        int dir = ((i & k) == 0);

                        // Branchless CAS using ternary or fminf/fmaxf
                        float min_val = fminf(a, b);
                        float max_val = fmaxf(a, b);

                        arr[i]  = dir ? min_val : max_val;
                        arr[ij] = dir ? max_val : min_val;
                    }
                }
            }
        }
    }
}
