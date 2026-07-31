// C5-REAL EXERGY CERTIFIED
#include <arm_neon.h>
#include <dispatch/dispatch.h>
#include <stdlib.h>

// [ULTRATHINK] Axiomas Ω15, Ω21, Ω23, Ω26: GEMM Micro-Kernel (General Matrix Multiply)
// TLP: Grand Central Dispatch
// GotoBLAS Data Packing: Erradicación de TLB Misses (Memoria Secuencial Continua)
// Hyper-ILP: 8x8 Register Blocking + vmlaq_laneq_f32

#define BLOCK_SIZE 128

void gemm_neon_gcd(const float *A, const float *B, float *C, int n) {
    int num_blocks = n / BLOCK_SIZE;

    // TLP: Distribuir bloques de filas 'i' en todos los Cores M3 (GCD)
    dispatch_apply(num_blocks, dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_HIGH, 0), ^(size_t bi) {
        int global_i = bi * BLOCK_SIZE;

        // Memoria Stack Alineada (L1/L2 Cache friendly)
        float __attribute__((aligned(64))) packed_A[BLOCK_SIZE * BLOCK_SIZE];
        float __attribute__((aligned(64))) packed_B[BLOCK_SIZE * BLOCK_SIZE];

        for (int global_k = 0; global_k < n; global_k += BLOCK_SIZE) {

            // [DATA PACKING] Panel A: Empaquetar bloque (BLOCK_SIZE x BLOCK_SIZE)
            // Formato: 8x1 bloques columna para acceso vectorial continuo en el K-loop
            int a_idx = 0;
            for (int i = 0; i < BLOCK_SIZE; i += 8) {
                for (int k = 0; k < BLOCK_SIZE; k++) {
                    for (int ii = 0; ii < 8; ii++) {
                        packed_A[a_idx++] = A[(global_i + i + ii) * n + (global_k + k)];
                    }
                }
            }

            for (int global_j = 0; global_j < n; global_j += BLOCK_SIZE) {

                // [DATA PACKING] Panel B: Empaquetar bloque (BLOCK_SIZE x BLOCK_SIZE)
                // Formato: 1x8 bloques fila para acceso vectorial continuo
                int b_idx = 0;
                for (int j = 0; j < BLOCK_SIZE; j += 8) {
                    for (int k = 0; k < BLOCK_SIZE; k++) {
                        for (int jj = 0; jj < 8; jj++) {
                            packed_B[b_idx++] = B[(global_k + k) * n + (global_j + j + jj)];
                        }
                    }
                }

                // Micro-Kernel 8x8 operando estrictamente sobre buffers contiguos L1
                for (int i_idx = 0, a_panel_offset = 0; i_idx < BLOCK_SIZE; i_idx += 8, a_panel_offset += 8 * BLOCK_SIZE) {
                    for (int j_idx = 0, b_panel_offset = 0; j_idx < BLOCK_SIZE; j_idx += 8, b_panel_offset += 8 * BLOCK_SIZE) {

                        const float* a_ptr = &packed_A[a_panel_offset];
                        const float* b_ptr = &packed_B[b_panel_offset];

                        // Cargar C
                        float32x4_t c00 = vld1q_f32(&C[(global_i + i_idx + 0)*n + global_j + j_idx]);
                        float32x4_t c01 = vld1q_f32(&C[(global_i + i_idx + 0)*n + global_j + j_idx + 4]);
                        float32x4_t c10 = vld1q_f32(&C[(global_i + i_idx + 1)*n + global_j + j_idx]);
                        float32x4_t c11 = vld1q_f32(&C[(global_i + i_idx + 1)*n + global_j + j_idx + 4]);
                        float32x4_t c20 = vld1q_f32(&C[(global_i + i_idx + 2)*n + global_j + j_idx]);
                        float32x4_t c21 = vld1q_f32(&C[(global_i + i_idx + 2)*n + global_j + j_idx + 4]);
                        float32x4_t c30 = vld1q_f32(&C[(global_i + i_idx + 3)*n + global_j + j_idx]);
                        float32x4_t c31 = vld1q_f32(&C[(global_i + i_idx + 3)*n + global_j + j_idx + 4]);
                        float32x4_t c40 = vld1q_f32(&C[(global_i + i_idx + 4)*n + global_j + j_idx]);
                        float32x4_t c41 = vld1q_f32(&C[(global_i + i_idx + 4)*n + global_j + j_idx + 4]);
                        float32x4_t c50 = vld1q_f32(&C[(global_i + i_idx + 5)*n + global_j + j_idx]);
                        float32x4_t c51 = vld1q_f32(&C[(global_i + i_idx + 5)*n + global_j + j_idx + 4]);
                        float32x4_t c60 = vld1q_f32(&C[(global_i + i_idx + 6)*n + global_j + j_idx]);
                        float32x4_t c61 = vld1q_f32(&C[(global_i + i_idx + 6)*n + global_j + j_idx + 4]);
                        float32x4_t c70 = vld1q_f32(&C[(global_i + i_idx + 7)*n + global_j + j_idx]);
                        float32x4_t c71 = vld1q_f32(&C[(global_i + i_idx + 7)*n + global_j + j_idx + 4]);

                        // K-Loop estrictamente secuencial O(1) memoria
                        for (int k = 0; k < BLOCK_SIZE; k++) {
                            // Carga vectorial (Sin TLB Misses)
                            float32x4_t a_vec0 = vld1q_f32(a_ptr); a_ptr += 4;
                            float32x4_t a_vec1 = vld1q_f32(a_ptr); a_ptr += 4;

                            float32x4_t b0 = vld1q_f32(b_ptr); b_ptr += 4;
                            float32x4_t b1 = vld1q_f32(b_ptr); b_ptr += 4;

                            // FMA Lane-Specific (Vector x Scalar)
                            c00 = vmlaq_laneq_f32(c00, b0, a_vec0, 0);
                            c01 = vmlaq_laneq_f32(c01, b1, a_vec0, 0);

                            c10 = vmlaq_laneq_f32(c10, b0, a_vec0, 1);
                            c11 = vmlaq_laneq_f32(c11, b1, a_vec0, 1);

                            c20 = vmlaq_laneq_f32(c20, b0, a_vec0, 2);
                            c21 = vmlaq_laneq_f32(c21, b1, a_vec0, 2);

                            c30 = vmlaq_laneq_f32(c30, b0, a_vec0, 3);
                            c31 = vmlaq_laneq_f32(c31, b1, a_vec0, 3);

                            c40 = vmlaq_laneq_f32(c40, b0, a_vec1, 0);
                            c41 = vmlaq_laneq_f32(c41, b1, a_vec1, 0);

                            c50 = vmlaq_laneq_f32(c50, b0, a_vec1, 1);
                            c51 = vmlaq_laneq_f32(c51, b1, a_vec1, 1);

                            c60 = vmlaq_laneq_f32(c60, b0, a_vec1, 2);
                            c61 = vmlaq_laneq_f32(c61, b1, a_vec1, 2);

                            c70 = vmlaq_laneq_f32(c70, b0, a_vec1, 3);
                            c71 = vmlaq_laneq_f32(c71, b1, a_vec1, 3);
                        }

                        // Guardar C
                        vst1q_f32(&C[(global_i + i_idx + 0)*n + global_j + j_idx], c00);
                        vst1q_f32(&C[(global_i + i_idx + 0)*n + global_j + j_idx + 4], c01);
                        vst1q_f32(&C[(global_i + i_idx + 1)*n + global_j + j_idx], c10);
                        vst1q_f32(&C[(global_i + i_idx + 1)*n + global_j + j_idx + 4], c11);
                        vst1q_f32(&C[(global_i + i_idx + 2)*n + global_j + j_idx], c20);
                        vst1q_f32(&C[(global_i + i_idx + 2)*n + global_j + j_idx + 4], c21);
                        vst1q_f32(&C[(global_i + i_idx + 3)*n + global_j + j_idx], c30);
                        vst1q_f32(&C[(global_i + i_idx + 3)*n + global_j + j_idx + 4], c31);
                        vst1q_f32(&C[(global_i + i_idx + 4)*n + global_j + j_idx], c40);
                        vst1q_f32(&C[(global_i + i_idx + 4)*n + global_j + j_idx + 4], c41);
                        vst1q_f32(&C[(global_i + i_idx + 5)*n + global_j + j_idx], c50);
                        vst1q_f32(&C[(global_i + i_idx + 5)*n + global_j + j_idx + 4], c51);
                        vst1q_f32(&C[(global_i + i_idx + 6)*n + global_j + j_idx], c60);
                        vst1q_f32(&C[(global_i + i_idx + 6)*n + global_j + j_idx + 4], c61);
                        vst1q_f32(&C[(global_i + i_idx + 7)*n + global_j + j_idx], c70);
                        vst1q_f32(&C[(global_i + i_idx + 7)*n + global_j + j_idx + 4], c71);
                    }
                }
            }
        }
    });
}
