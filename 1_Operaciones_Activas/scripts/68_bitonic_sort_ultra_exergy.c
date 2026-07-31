// C5-REAL EXERGY CERTIFIED
#include <arm_neon.h>
#include <stdint.h>
#include <math.h>
#include <dispatch/dispatch.h>

// [ULTRATHINK] Axioma Ω15 & Ω21: Bitonic Sort
// O(N log^2 N) Sorting network. Branchless. SIMD ILP Unrolled.

void bitonic_sort_neon(float *arr, int n) {
    // 128 hilos lógicos administrados por GCD en los Performance Cores del M1
    int chunks = 128;
    int vectors_per_chunk = (n / 32) / chunks;

    for (int k = 2; k <= n; k *= 2) {
        for (int j = k >> 1; j > 0; j = j >> 1) {

            // SIMD & GCD Path (Para saltos mayores a 16, la dirección es constante en el vector)
            if (j >= 16) {
                dispatch_apply(chunks, dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_HIGH, 0), ^(size_t c) {
                    int v_start = c * vectors_per_chunk;
                    int v_end = v_start + vectors_per_chunk;

                    for (int v = v_start; v < v_end; v++) {
                        int p = v * 16;

                        // Direccionamiento físico libre de colisiones O(1)
                        int block = p / j;
                        int offset = p & (j - 1);
                        int idx1 = (block * 2 * j) + offset;
                        int idx2 = idx1 + j;

                        int dir = ((idx1 & k) == 0);

                        float32x4_t v_a0 = vld1q_f32(&arr[idx1]);
                        float32x4_t v_b0 = vld1q_f32(&arr[idx2]);
                        float32x4_t v_a1 = vld1q_f32(&arr[idx1 + 4]);
                        float32x4_t v_b1 = vld1q_f32(&arr[idx2 + 4]);
                        float32x4_t v_a2 = vld1q_f32(&arr[idx1 + 8]);
                        float32x4_t v_b2 = vld1q_f32(&arr[idx2 + 8]);
                        float32x4_t v_a3 = vld1q_f32(&arr[idx1 + 12]);
                        float32x4_t v_b3 = vld1q_f32(&arr[idx2 + 12]);

                        float32x4_t min0 = vminq_f32(v_a0, v_b0);
                        float32x4_t max0 = vmaxq_f32(v_a0, v_b0);
                        float32x4_t min1 = vminq_f32(v_a1, v_b1);
                        float32x4_t max1 = vmaxq_f32(v_a1, v_b1);
                        float32x4_t min2 = vminq_f32(v_a2, v_b2);
                        float32x4_t max2 = vmaxq_f32(v_a2, v_b2);
                        float32x4_t min3 = vminq_f32(v_a3, v_b3);
                        float32x4_t max3 = vmaxq_f32(v_a3, v_b3);

                        if (dir) {
                            vst1q_f32(&arr[idx1], min0);
                            vst1q_f32(&arr[idx2], max0);
                            vst1q_f32(&arr[idx1+4], min1);
                            vst1q_f32(&arr[idx2+4], max1);
                            vst1q_f32(&arr[idx1+8], min2);
                            vst1q_f32(&arr[idx2+8], max2);
                            vst1q_f32(&arr[idx1+12], min3);
                            vst1q_f32(&arr[idx2+12], max3);
                        } else {
                            vst1q_f32(&arr[idx1], max0);
                            vst1q_f32(&arr[idx2], min0);
                            vst1q_f32(&arr[idx1+4], max1);
                            vst1q_f32(&arr[idx2+4], min1);
                            vst1q_f32(&arr[idx1+8], max2);
                            vst1q_f32(&arr[idx2+8], min2);
                            vst1q_f32(&arr[idx1+12], max3);
                            vst1q_f32(&arr[idx2+12], min3);
                        }
                    }
                });
            } else {
                // Secuencial para granularidad extrema (j < 16)
                for (int i = 0; i < n; i += 2 * j) {
                    for (int l = 0; l < j; l++) {
                        int idx1 = i + l;
                        int idx2 = idx1 + j;

                        float a = arr[idx1];
                        float b = arr[idx2];
                        int dir = ((idx1 & k) == 0);

                        float min_val = fminf(a, b);
                        float max_val = fmaxf(a, b);

                        arr[idx1]  = dir ? min_val : max_val;
                        arr[idx2] = dir ? max_val : min_val;
                    }
                }
            }
        }
    }
}
