// C5-REAL EXERGY CERTIFIED
/*
 * TERCER MEJOR SCRIPT DE LA HISTORIA: XORSHIFT PRNG
 * Monorepo: Teorema-Robinson-Moskv
 * Target: macOS ARM64 NEON / Apple Silicon
 * Axiomas Ω15 (Hardware Exergy) & Ω21 (ILP Loop Unrolling)
 */

#include <stdint.h>
#include <stddef.h>

#if defined(__ARM_NEON) || defined(__ARM_NEON__)
#include <arm_neon.h>
#endif

// 1. Algoritmo Legendario: Xorshift64 de George Marsaglia (C Puro)
uint64_t xorshift64_step(uint64_t *state) {
    uint64_t x = *state;
    x ^= x << 13;
    x ^= x >> 7;
    x ^= x << 17;
    return *state = x;
}

// Wrapper para buffers lineales (Classic)
void xorshift_array_classic(uint64_t* out, size_t count, uint64_t initial_seed) {
    uint64_t state = initial_seed ? initial_seed : 0xDEADBEEFCAFEBABEULL;
    for (size_t i = 0; i < count; i++) {
        out[i] = xorshift64_step(&state);
    }
}

// 2. Hardware Exergy (Axioma Ω21): ARM NEON con Loop Unrolling 4x
// Mantiene 8 estados de 64-bits en paralelo. Dispara 512 bits de entropía por ciclo.
#if defined(__ARM_NEON) || defined(__ARM_NEON__)
void xorshift_array_neon(uint64_t* out, size_t count, const uint64_t* initial_seeds) {
    // Carga de 8 semillas independientes en 4 registros superescalares
    uint64x2_t s0 = vld1q_u64(initial_seeds);
    uint64x2_t s1 = vld1q_u64(initial_seeds + 2);
    uint64x2_t s2 = vld1q_u64(initial_seeds + 4);
    uint64x2_t s3 = vld1q_u64(initial_seeds + 6);

    size_t i = 0;
    // Unrolling masivo: 512 bits procesados en paralelo (ILP)
    for (; i + 7 < count; i += 8) {
        // x ^= x << 13
        s0 = veorq_u64(s0, vshlq_n_u64(s0, 13));
        s1 = veorq_u64(s1, vshlq_n_u64(s1, 13));
        s2 = veorq_u64(s2, vshlq_n_u64(s2, 13));
        s3 = veorq_u64(s3, vshlq_n_u64(s3, 13));

        // x ^= x >> 7
        s0 = veorq_u64(s0, vshrq_n_u64(s0, 7));
        s1 = veorq_u64(s1, vshrq_n_u64(s1, 7));
        s2 = veorq_u64(s2, vshrq_n_u64(s2, 7));
        s3 = veorq_u64(s3, vshrq_n_u64(s3, 7));

        // x ^= x << 17
        s0 = veorq_u64(s0, vshlq_n_u64(s0, 17));
        s1 = veorq_u64(s1, vshlq_n_u64(s1, 17));
        s2 = veorq_u64(s2, vshlq_n_u64(s2, 17));
        s3 = veorq_u64(s3, vshlq_n_u64(s3, 17));

        // Inyección consecutiva en memoria L1/L2
        vst1q_u64(out + i, s0);
        vst1q_u64(out + i + 2, s1);
        vst1q_u64(out + i + 4, s2);
        vst1q_u64(out + i + 6, s3);
    }

    // Residual (Cola N % 8)
    if (i < count) {
        uint64_t tmp[8];
        s0 = veorq_u64(s0, vshlq_n_u64(s0, 13));
        s0 = veorq_u64(s0, vshrq_n_u64(s0, 7));
        s0 = veorq_u64(s0, vshlq_n_u64(s0, 17));

        s1 = veorq_u64(s1, vshlq_n_u64(s1, 13));
        s1 = veorq_u64(s1, vshrq_n_u64(s1, 7));
        s1 = veorq_u64(s1, vshlq_n_u64(s1, 17));

        s2 = veorq_u64(s2, vshlq_n_u64(s2, 13));
        s2 = veorq_u64(s2, vshrq_n_u64(s2, 7));
        s2 = veorq_u64(s2, vshlq_n_u64(s2, 17));

        s3 = veorq_u64(s3, vshlq_n_u64(s3, 13));
        s3 = veorq_u64(s3, vshrq_n_u64(s3, 7));
        s3 = veorq_u64(s3, vshlq_n_u64(s3, 17));

        vst1q_u64(tmp, s0);
        vst1q_u64(tmp + 2, s1);
        vst1q_u64(tmp + 4, s2);
        vst1q_u64(tmp + 6, s3);

        for (size_t j = 0; i < count; i++, j++) {
            out[i] = tmp[j];
        }
    }
}
#else
void xorshift_array_neon(uint64_t* out, size_t count, const uint64_t* initial_seeds) {
    xorshift_array_classic(out, count, initial_seeds[0]); // Fallback C5-SIM
}
#endif
