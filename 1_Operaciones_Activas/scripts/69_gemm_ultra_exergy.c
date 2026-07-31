// C5-REAL EXERGY CERTIFIED
#include <arm_neon.h>
#include <dispatch/dispatch.h>
#include <stdlib.h>

// [ULTRATHINK] Axiomas Ω15, Ω21, Ω23: GEMM Micro-Kernel (General Matrix Multiply)
// TLP: Grand Central Dispatch (Outer blocks)
// Cache Locality: Block Tiling (BLOCK_SIZE)
// ILP: 4x4 Register Blocking FMA (vmlaq_n_f32)

#define BLOCK_SIZE 128 // Tamaño óptimo para L1 Cache

void gemm_neon_gcd(const float *A, const float *B, float *C, int n) {
    // Aseguramos que N es múltiplo de BLOCK_SIZE en el frontend
    int num_blocks = n / BLOCK_SIZE;

    // TLP: Distribuir bloques de filas 'i' en todos los Cores M1 (GCD)
    dispatch_apply(num_blocks, dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_HIGH, 0), ^(size_t bi) {
        int i_start = bi * BLOCK_SIZE;
        int i_end = i_start + BLOCK_SIZE;

        // Cache Tiling: Iteramos por baldosas para maximizar Cache Hits
        for (int bj = 0; bj < n; bj += BLOCK_SIZE) {
            for (int bk = 0; bk < n; bk += BLOCK_SIZE) {

                // Micro-Kernel 4x4 ILP (Inner Loop Unrolling)
                for (int i = i_start; i < i_end; i += 4) {
                    for (int j = bj; j < bj + BLOCK_SIZE; j += 4) {

                        // Cargar bloque 4x4 de C en 4 registros NEON (16 floats)
                        float32x4_t c0 = vld1q_f32(&C[(i+0)*n + j]);
                        float32x4_t c1 = vld1q_f32(&C[(i+1)*n + j]);
                        float32x4_t c2 = vld1q_f32(&C[(i+2)*n + j]);
                        float32x4_t c3 = vld1q_f32(&C[(i+3)*n + j]);

                        for (int k = bk; k < bk + BLOCK_SIZE; k++) {
                            // Cargar 1 vector (4 floats) de la fila K de B
                            float32x4_t b0 = vld1q_f32(&B[k*n + j]);

                            // FMA (Fused Multiply-Add): C += A * B
                            // Broadcast A[i,k] escalar al vector B[k,j:j+3]
                            c0 = vmlaq_n_f32(c0, b0, A[(i+0)*n + k]);
                            c1 = vmlaq_n_f32(c1, b0, A[(i+1)*n + k]);
                            c2 = vmlaq_n_f32(c2, b0, A[(i+2)*n + k]);
                            c3 = vmlaq_n_f32(c3, b0, A[(i+3)*n + k]);
                        }

                        // Guardar bloque 4x4 de vuelta a Memoria
                        vst1q_f32(&C[(i+0)*n + j], c0);
                        vst1q_f32(&C[(i+1)*n + j], c1);
                        vst1q_f32(&C[(i+2)*n + j], c2);
                        vst1q_f32(&C[(i+3)*n + j], c3);
                    }
                }
            }
        }
    });
}
