// C5-REAL EXERGY CERTIFIED
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <stdint.h>

// BFT Zero-Tolerance Guard
// If condition is false (0), the OS kernel murders the process.
void bft_assert(int condition, const char* constraint_name) {
    if (!condition) {
        fprintf(stderr, "\n[CORTEX-GUARD: FATAL] Invariant Violated: %s\n", constraint_name);
        fprintf(stderr, "[CORTEX-GUARD: FATAL] Escalamiento BFT. Detonando SIGABRT (Core Dump)...\n\n");
        fflush(stderr);
        abort(); // Invocación POSIX. Intérprete Python aniquilado.
    }
}
