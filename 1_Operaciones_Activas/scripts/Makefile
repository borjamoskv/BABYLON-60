# [ULTRATHINK] Axioma Ω25: Deterministic Build & Orphan Eradication
# Axioma Ω24: Zero-Residual Macro-Exergy (Build to /tmp/)

CC = clang
CFLAGS = -O3 -mcpu=apple-m1 -fvectorize -funroll-loops -fblocks -dynamiclib
BUILD_DIR = /tmp/exergy_builds

# Fuentes
SRC_XORSHIFT = 67_xorshift_ultra_exergy.c
SRC_BITONIC  = 68_bitonic_sort_ultra_exergy.c
SRC_GEMM     = 69_gemm_ultra_exergy.c

# Binarios de salida (Zero-Residual en /tmp/)
OUT_XORSHIFT = $(BUILD_DIR)/libxorshift_neon.dylib
OUT_BITONIC  = $(BUILD_DIR)/libbitonic_neon.dylib
OUT_GEMM     = $(BUILD_DIR)/libgemm_neon.dylib

all: init_build_dir $(OUT_XORSHIFT) $(OUT_BITONIC) $(OUT_GEMM)

init_build_dir:
	@mkdir -p $(BUILD_DIR)

$(OUT_XORSHIFT): $(SRC_XORSHIFT)
	@echo "--- ⚙️ FORJANDO SILICIO: XORSHIFT ---"
	$(CC) $(CFLAGS) -o $@ $^

$(OUT_BITONIC): $(SRC_BITONIC)
	@echo "--- ⚙️ FORJANDO SILICIO: BITONIC SORT ---"
	$(CC) $(CFLAGS) -o $@ $^

$(OUT_GEMM): $(SRC_GEMM)
	@echo "--- ⚙️ FORJANDO SILICIO: GEMM MICRO-KERNEL ---"
	$(CC) $(CFLAGS) -o $@ $^

clean:
	@echo "--- 🧹 PURGANDO ENTROPÍA (Axioma Ω24) ---"
	rm -rf $(BUILD_DIR)

.PHONY: all clean init_build_dir
