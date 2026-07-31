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
    // Procesamos tensores de 128 bits (16 bytes = 2 uint64_t) por instrucción base
    size_t i = 0;
    for (; i + 1 < count; i += 2) {
        // Carga 128 bits (2 u64) en el registro NEON Q
        uint8x16_t vec = vld1q_u8((const uint8_t*)(data + i));

        // El milagro del silicio: Cuenta los bits activos en cada byte individualmente (vcnt)
        uint8x16_t cnt = vcntq_u8(vec);

        // Sumamos los bytes en mitades de 64 bits utilizando el Add Long (Paddl)
        uint16x8_t sum16 = vpaddlq_u8(cnt);
        uint32x4_t sum32 = vpaddlq_u16(sum16);
        uint64x2_t sum64 = vpaddlq_u32(sum32);

        // Descargamos el resultado
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
