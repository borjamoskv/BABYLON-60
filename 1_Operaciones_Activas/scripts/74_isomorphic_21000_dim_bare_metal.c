// C5-REAL EXERGY CERTIFIED
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <math.h>

#define TABLE_SIZE 65536
#define PASSES 1000 // 1000 iterations for stable bare-metal measurement

// Ultra-fast xorshift32 for deterministic pseudo-random challenge generation
uint32_t xorshift32(uint32_t *state) {
    uint32_t x = *state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    return *state = x;
}

int main() {
    printf("================================================================================\n");
    printf("LOGUP FRACTIONAL SUM BARE-METAL C STRESS TEST\n");
    printf("================================================================================\n");

    // Pre-allocate the lookup table
    uint32_t *table = (uint32_t *)malloc(TABLE_SIZE * sizeof(uint32_t));
    if (!table) {
        fprintf(stderr, "Memory allocation failed.\n");
        return 1;
    }

    // Populate with pseudo-hashes (equivalent to token keys)
    uint32_t prng_state = 0xDEADBEEF;
    for (int i = 0; i < TABLE_SIZE; i++) {
        table[i] = (xorshift32(&prng_state) % 1000000) + 1;
    }

    struct timespec start, end;
    double total_time = 0.0;
    double global_acc = 0.0;

    // Run PASSES iterations to get a highly stable measurement
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int p = 0; p < PASSES; p++) {
        uint32_t challenge = xorshift32(&prng_state) % 1000000000;
        double acc = 0.0;

        // Hot loop: LogUp fractional sum
        #pragma GCC unroll 8
        for (int i = 0; i < TABLE_SIZE; i++) {
            acc += 1.0 / (double)(challenge + table[i]);
        }
        global_acc += acc;
    }

    clock_gettime(CLOCK_MONOTONIC, &end);
    total_time = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;

    double avg_latency_ms = (total_time / PASSES) * 1000.0;
    double total_lookups = (double)TABLE_SIZE * PASSES;
    double throughput = total_lookups / total_time;

    printf("■ Passes Executed            : %d\n", PASSES);
    printf("■ Table Size                 : %d\n", TABLE_SIZE);
    printf("■ Bare-Metal Avg Latency     : %.6f ms\n", avg_latency_ms);
    printf("■ Hardware Throughput        : %.2f lookups/sec\n", throughput);
    printf("■ LogUp Accumulator Verify   : %.12e\n", global_acc);
    printf("================================================================================\n");

    free(table);
    return 0;
}
