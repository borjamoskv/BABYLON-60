// C5-REAL EXERGY CERTIFIED
#include <arm_neon.h>
#include <dispatch/dispatch.h>
#include <stdlib.h>

// [ULTRATHINK] Axiomas Ω15, Ω21, Ω23: GEMM Micro-Kernel (General Matrix Multiply)
// TLP: Grand Central Dispatch (Outer blocks)
// Cache Locality: Block Tiling (BLOCK_SIZE)
// Hyper-ILP: 8x8 Register Blocking FMA (vmlaq_n_f32) - 16 vectores C, 2 vectores B.

#define BLOCK_SIZE 128 // Tamaño óptimo para L1 Cache. Múltiplo de 8.

void gemm_neon_gcd(const float *A, const float *B, float *C, int n) {
    int num_blocks = n / BLOCK_SIZE;

    // TLP: Distribuir bloques de filas 'i' en todos los Cores M1 (GCD)
    dispatch_apply(num_blocks, dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_HIGH, 0), ^(size_t bi) {
        int i_start = bi * BLOCK_SIZE;
        int i_end = i_start + BLOCK_SIZE;

        // Cache Tiling: Iteramos por baldosas para maximizar Cache Hits
        for (int bj = 0; bj < n; bj += BLOCK_SIZE) {
            for (int bk = 0; bk < n; bk += BLOCK_SIZE) {

                // Micro-Kernel 8x8 Hyper-ILP (Inner Loop Unrolling x8)
                for (int i = i_start; i < i_end; i += 8) {
                    for (int j = bj; j < bj + BLOCK_SIZE; j += 8) {

                        // Cargar bloque 8x8 de C en 16 registros NEON (64 floats)
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

                        for (int k = bk; k < bk + BLOCK_SIZE; k++) {
                            // Cargar 2 vectores (8 floats) de la fila K de B
                            float32x4_t b0 = vld1q_f32(&B[k*n + j]);
                            float32x4_t b1 = vld1q_f32(&B[k*n + j + 4]);

                            // FMA (Fused Multiply-Add): C += A * B
                            // Broadcast A[i,k] escalar al vector B[k,j:j+7]
                            float a0 = A[(i+0)*n + k];
                            c00 = vmlaq_n_f32(c00, b0, a0);
                            c01 = vmlaq_n_f32(c01, b1, a0);

                            float a1 = A[(i+1)*n + k];
                            c10 = vmlaq_n_f32(c10, b0, a1);
                            c11 = vmlaq_n_f32(c11, b1, a1);

                            float a2 = A[(i+2)*n + k];
                            c20 = vmlaq_n_f32(c20, b0, a2);
                            c21 = vmlaq_n_f32(c21, b1, a2);

                            float a3 = A[(i+3)*n + k];
                            c30 = vmlaq_n_f32(c30, b0, a3);
                            c31 = vmlaq_n_f32(c31, b1, a3);

                            float a4 = A[(i+4)*n + k];
                            c40 = vmlaq_n_f32(c40, b0, a4);
                            c41 = vmlaq_n_f32(c41, b1, a4);

                            float a5 = A[(i+5)*n + k];
                            c50 = vmlaq_n_f32(c50, b0, a5);
                            c51 = vmlaq_n_f32(c51, b1, a5);

                            float a6 = A[(i+6)*n + k];
                            c60 = vmlaq_n_f32(c60, b0, a6);
                            c61 = vmlaq_n_f32(c61, b1, a6);

                            float a7 = A[(i+7)*n + k];
                            c70 = vmlaq_n_f32(c70, b0, a7);
                            c71 = vmlaq_n_f32(c71, b1, a7);
                        }

                        // Guardar bloque 8x8 de vuelta a Memoria
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
