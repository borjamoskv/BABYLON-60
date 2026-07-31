// C5-REAL EXERGY CERTIFIED
#include <arm_neon.h>
#include <dispatch/dispatch.h>
#include <stdlib.h>

// [ULTRATHINK] Axiomas Ω15, Ω21, Ω23, Ω26: GEMM Micro-Kernel (General Matrix Multiply)
// TLP: Grand Central Dispatch
// Cache Locality: Block Tiling
// Hyper-ILP: 8x8 Register Blocking FMA + Temporal Unrolling (Kx4) + Prefetching

#define BLOCK_SIZE 128

// Macro para ejecutar un paso K del bucle (Ocultando Latencia FMA)
#define K_STEP(step) \
    b0 = vld1q_f32(&B[(k+step)*n + j]); \
    b1 = vld1q_f32(&B[(k+step)*n + j + 4]); \
    c00 = vmlaq_n_f32(c00, b0, A[(i+0)*n + k+step]); \
    c01 = vmlaq_n_f32(c01, b1, A[(i+0)*n + k+step]); \
    c10 = vmlaq_n_f32(c10, b0, A[(i+1)*n + k+step]); \
    c11 = vmlaq_n_f32(c11, b1, A[(i+1)*n + k+step]); \
    c20 = vmlaq_n_f32(c20, b0, A[(i+2)*n + k+step]); \
    c21 = vmlaq_n_f32(c21, b1, A[(i+2)*n + k+step]); \
    c30 = vmlaq_n_f32(c30, b0, A[(i+3)*n + k+step]); \
    c31 = vmlaq_n_f32(c31, b1, A[(i+3)*n + k+step]); \
    c40 = vmlaq_n_f32(c40, b0, A[(i+4)*n + k+step]); \
    c41 = vmlaq_n_f32(c41, b1, A[(i+4)*n + k+step]); \
    c50 = vmlaq_n_f32(c50, b0, A[(i+5)*n + k+step]); \
    c51 = vmlaq_n_f32(c51, b1, A[(i+5)*n + k+step]); \
    c60 = vmlaq_n_f32(c60, b0, A[(i+6)*n + k+step]); \
    c61 = vmlaq_n_f32(c61, b1, A[(i+6)*n + k+step]); \
    c70 = vmlaq_n_f32(c70, b0, A[(i+7)*n + k+step]); \
    c71 = vmlaq_n_f32(c71, b1, A[(i+7)*n + k+step]);

void gemm_neon_gcd(const float *A, const float *B, float *C, int n) {
    int num_blocks = n / BLOCK_SIZE;

    dispatch_apply(num_blocks, dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_HIGH, 0), ^(size_t bi) {
        int i_start = bi * BLOCK_SIZE;
        int i_end = i_start + BLOCK_SIZE;

        for (int bj = 0; bj < n; bj += BLOCK_SIZE) {
            for (int bk = 0; bk < n; bk += BLOCK_SIZE) {

                // Micro-Kernel 8x8 con K-Loop Unrolling x4
                for (int i = i_start; i < i_end; i += 8) {
                    for (int j = bj; j < bj + BLOCK_SIZE; j += 8) {

                        // Prefetching C
                        __builtin_prefetch(&C[(i+0)*n + j], 1, 3);
                        __builtin_prefetch(&C[(i+4)*n + j], 1, 3);

                        float32x4_t c00 = vld1q_f32(&C[(i+0)*n + j]);
                        float32x4_t c01 = vld1q_f32(&C[(i+0)*n + j + 4]);
                        float32x4_t c10 = vld1q_f32(&C[(i+1)*n + j]);
                        float32x4_t c11 = vld1q_f32(&C[(i+1)*n + j + 4]);
                        float32x4_t c20 = vld1q_f32(&C[(i+2)*n + j]);
                        float32x4_t c21 = vld1q_f32(&C[(i+2)*n + j + 4]);
                        float32x4_t c30 = vld1q_f32(&C[(i+3)*n + j]);
                        float32x4_t c31 = vld1q_f32(&C[(i+3)*n + j + 4]);

                        float32x4_t c40 = vld1q_f32(&C[(i+4)*n + j]);
                        float32x4_t c41 = vld1q_f32(&C[(i+4)*n + j + 4]);
                        float32x4_t c50 = vld1q_f32(&C[(i+5)*n + j]);
                        float32x4_t c51 = vld1q_f32(&C[(i+5)*n + j + 4]);
                        float32x4_t c60 = vld1q_f32(&C[(i+6)*n + j]);
                        float32x4_t c61 = vld1q_f32(&C[(i+6)*n + j + 4]);
                        float32x4_t c70 = vld1q_f32(&C[(i+7)*n + j]);
                        float32x4_t c71 = vld1q_f32(&C[(i+7)*n + j + 4]);

                        for (int k = bk; k < bk + BLOCK_SIZE; k += 4) {
                            // Prefetching A y B con antelación (Tolerancia Latencia)
                            __builtin_prefetch(&A[(i+0)*n + k + 32], 0, 1);
                            __builtin_prefetch(&B[(k+16)*n + j], 0, 1);

                            float32x4_t b0, b1;

                            K_STEP(0)
                            K_STEP(1)
                            K_STEP(2)
                            K_STEP(3)
                        }

                        vst1q_f32(&C[(i+0)*n + j], c00);
                        vst1q_f32(&C[(i+0)*n + j + 4], c01);
                        vst1q_f32(&C[(i+1)*n + j], c10);
                        vst1q_f32(&C[(i+1)*n + j + 4], c11);
                        vst1q_f32(&C[(i+2)*n + j], c20);
                        vst1q_f32(&C[(i+2)*n + j + 4], c21);
                        vst1q_f32(&C[(i+3)*n + j], c30);
                        vst1q_f32(&C[(i+3)*n + j + 4], c31);

                        vst1q_f32(&C[(i+4)*n + j], c40);
                        vst1q_f32(&C[(i+4)*n + j + 4], c41);
                        vst1q_f32(&C[(i+5)*n + j], c50);
                        vst1q_f32(&C[(i+5)*n + j + 4], c51);
                        vst1q_f32(&C[(i+6)*n + j], c60);
                        vst1q_f32(&C[(i+6)*n + j + 4], c61);
                        vst1q_f32(&C[(i+7)*n + j], c70);
                        vst1q_f32(&C[(i+7)*n + j + 4], c71);
                    }
                }
            }
        }
    });
}
