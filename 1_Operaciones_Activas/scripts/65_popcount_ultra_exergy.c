// C5-REAL EXERGY CERTIFIED
/*
 * SEGUNDO MEJOR SCRIPT DE LA HISTORIA: HAMMING WEIGHT / POPCOUNT
 * Monorepo: Teorema-Robinson-Moskv
 * Target: macOS ARM64 NEON / Apple Silicon
 * Axioma Ω15 (Hardware Exergy Maximization)
 */

#include <stdint.h>
#include <stddef.h>

#if defined(__ARM_NEON) || defined(__ARM_NEON__)
#include <arm_neon.h>
#endif

// 1. Algoritmo Legendario: Wegner / Kernighan / Hamming Parallel Bit Hack
// Opera en O(1) tiempo independientemente de los bits activos usando paralelismo de bits
uint64_t popcount_64_classic(uint64_t x) {
    x -= (x >> 1) & 0x5555555555555555ULL;
    x = (x & 0x3333333333333333ULL) + ((x >> 2) & 0x3333333333333333ULL);
    x = (x + (x >> 4)) & 0x0f0f0f0f0f0f0f0fULL;
    return (x * 0x0101010101010101ULL) >> 56;
}

// Wrapper para buffers lineales (Classic)
void popcount_array_classic(const uint64_t* data, size_t count, uint64_t* out) {
    for (size_t i = 0; i < count; i++) {
        out[i] = popcount_64_classic(data[i]);
    }
}

// 2. Hardware Exergy (Axioma Ω15): ARM NEON vcntq_u8
// Directamente mapeado a los transistores (Instrucción de silicio de recuento)
#if defined(__ARM_NEON) || defined(__ARM_NEON__)
void popcount_array_neon(const uint64_t* data, size_t count, uint64_t* out) {
    // Bucle Principal: Loop Unrolling 4x (Procesa 512 bits / 8 uint64_t por salto)
    // Permite al procesador M1 super-escalar cargar en memoria L1 y pipelining asíncrono
    size_t i = 0;
    for (; i + 7 < count; i += 8) {
        // Carga paralela de 512 bits
        uint8x16_t vec0 = vld1q_u8((const uint8_t*)(data + i));
        uint8x16_t vec1 = vld1q_u8((const uint8_t*)(data + i + 2));
        uint8x16_t vec2 = vld1q_u8((const uint8_t*)(data + i + 4));
        uint8x16_t vec3 = vld1q_u8((const uint8_t*)(data + i + 6));

        // ILP Masivo: El procesador puede encolar estas 4 instrucciones independientes
        uint8x16_t cnt0 = vcntq_u8(vec0);
        uint8x16_t cnt1 = vcntq_u8(vec1);
        uint8x16_t cnt2 = vcntq_u8(vec2);
        uint8x16_t cnt3 = vcntq_u8(vec3);

        // Padding a 16-bits
        uint16x8_t sum16_0 = vpaddlq_u8(cnt0);
        uint16x8_t sum16_1 = vpaddlq_u8(cnt1);
        uint16x8_t sum16_2 = vpaddlq_u8(cnt2);
        uint16x8_t sum16_3 = vpaddlq_u8(cnt3);

        // Padding a 32-bits
        uint32x4_t sum32_0 = vpaddlq_u16(sum16_0);
        uint32x4_t sum32_1 = vpaddlq_u16(sum16_1);
        uint32x4_t sum32_2 = vpaddlq_u16(sum16_2);
        uint32x4_t sum32_3 = vpaddlq_u16(sum16_3);

        // Padding Final a 64-bits
        uint64x2_t sum64_0 = vpaddlq_u32(sum32_0);
        uint64x2_t sum64_1 = vpaddlq_u32(sum32_1);
        uint64x2_t sum64_2 = vpaddlq_u32(sum32_2);
        uint64x2_t sum64_3 = vpaddlq_u32(sum32_3);

        // Vaciado en memoria L1 consecutivo
        vst1q_u64(out + i, sum64_0);
        vst1q_u64(out + i + 2, sum64_1);
        vst1q_u64(out + i + 4, sum64_2);
        vst1q_u64(out + i + 6, sum64_3);
    }

    // Cola Residual NEON 1x (Para los elementos N % 8)
    for (; i + 1 < count; i += 2) {
        uint8x16_t vec = vld1q_u8((const uint8_t*)(data + i));
        uint8x16_t cnt = vcntq_u8(vec);
        uint16x8_t sum16 = vpaddlq_u8(cnt);
        uint32x4_t sum32 = vpaddlq_u16(sum16);
        uint64x2_t sum64 = vpaddlq_u32(sum32);
        vst1q_u64(out + i, sum64);
    }
    // Procesamiento residual
    for (; i < count; i++) {
        out[i] = popcount_64_classic(data[i]);
    }
}
#else
void popcount_array_neon(const uint64_t* data, size_t count, uint64_t* out) {
    popcount_array_classic(data, count, out); // Fallback C5-SIM
}
#endif
