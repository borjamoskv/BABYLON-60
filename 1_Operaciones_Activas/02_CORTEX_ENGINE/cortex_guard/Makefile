# Axiom Ω25 Deterministic Build
CC = clang
CFLAGS = -O3 -Wall -Wextra -dynamiclib

TARGET = libcortex_guard.dylib
SRC = cortex_guard.c

build:
	@echo "[CORTEX] Construyendo vanguardia BFT (cortex_guard)..."
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET)
	@echo "[PASS] libcortex_guard.dylib generado determinísticamente."

clean:
	@echo "[CORTEX] Ejecutando purga termodinámica (Ω24)..."
	rm -f $(TARGET)
