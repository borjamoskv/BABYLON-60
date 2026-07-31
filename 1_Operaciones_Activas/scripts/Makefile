# [ULTRATHINK] Axioma Ω25: Deterministic Build & Orphan Eradication
# Axioma Ω24: Zero-Residual Macro-Exergy (Build to /tmp/)

CC = clang
CFLAGS = -O3 -mcpu=apple-m1 -ffast-math -dynamiclib
BUILD_DIR = /tmp/exergy_builds

# Fuentes
SRC_Q_RSQRT     = 61_q_rsqrt_neon.c
SRC_Q_RSQRT_FMA = 61_q_rsqrt_neon_fma.c
SRC_PRIMITIVES  = 64_cortex_primitives_simd.c
SRC_POPCOUNT    = 65_popcount_ultra_exergy.c
SRC_XORSHIFT    = 67_xorshift_ultra_exergy.c
SRC_BITONIC     = 68_bitonic_sort_ultra_exergy.c
SRC_GEMM        = 69_gemm_ultra_exergy.c
SRC_SOFTMAX     = 70_softmax_ultra_exergy.c

# Binarios de salida (Zero-Residual en /tmp/)
OUT_Q_RSQRT     = $(BUILD_DIR)/libq_rsqrt_neon.dylib
OUT_Q_RSQRT_FMA = $(BUILD_DIR)/libq_rsqrt_neon_fma.dylib
OUT_PRIMITIVES  = $(BUILD_DIR)/libcortex_primitives_simd.dylib
OUT_POPCOUNT    = $(BUILD_DIR)/libpopcount_neon.dylib
OUT_XORSHIFT    = $(BUILD_DIR)/libxorshift_neon.dylib
OUT_BITONIC     = $(BUILD_DIR)/libbitonic_neon.dylib
OUT_GEMM        = $(BUILD_DIR)/libgemm_ultra_exergy.dylib
OUT_SOFTMAX     = $(BUILD_DIR)/libsoftmax_neon.dylib

ALL_TARGETS = $(OUT_Q_RSQRT) $(OUT_Q_RSQRT_FMA) $(OUT_PRIMITIVES) $(OUT_POPCOUNT) $(OUT_XORSHIFT) $(OUT_BITONIC) $(OUT_GEMM) $(OUT_SOFTMAX)

all: init_build_dir $(ALL_TARGETS)

init_build_dir:
	@mkdir -p $(BUILD_DIR)

$(OUT_Q_RSQRT): $(SRC_Q_RSQRT)
	@echo "--- ⚙️ FORJANDO SILICIO: Q_RSQRT ---"
	$(CC) $(CFLAGS) -o $@ $^

$(OUT_Q_RSQRT_FMA): $(SRC_Q_RSQRT_FMA)
	@echo "--- ⚙️ FORJANDO SILICIO: Q_RSQRT FMA ---"
	$(CC) $(CFLAGS) -o $@ $^

$(OUT_PRIMITIVES): $(SRC_PRIMITIVES)
	@echo "--- ⚙️ FORJANDO SILICIO: CORTEX PRIMITIVES SIMD ---"
	$(CC) $(CFLAGS) -o $@ $^

$(OUT_POPCOUNT): $(SRC_POPCOUNT)
	@echo "--- ⚙️ FORJANDO SILICIO: POPCOUNT ---"
	$(CC) $(CFLAGS) -o $@ $^

$(OUT_XORSHIFT): $(SRC_XORSHIFT)
	@echo "--- ⚙️ FORJANDO SILICIO: XORSHIFT ---"
	$(CC) $(CFLAGS) -o $@ $^

$(OUT_BITONIC): $(SRC_BITONIC)
	@echo "--- ⚙️ FORJANDO SILICIO: BITONIC SORT ---"
	$(CC) $(CFLAGS) -o $@ $^

$(OUT_GEMM): $(SRC_GEMM)
	@echo "--- ⚙️ FORJANDO SILICIO: GEMM MICRO-KERNEL ---"
	$(CC) $(CFLAGS) -o $@ $^

$(OUT_SOFTMAX): $(SRC_SOFTMAX)
	@echo "--- ⚙️ FORJANDO SILICIO: FAST-SOFTMAX NEON FMA ---"
	$(CC) $(CFLAGS) -o $@ $^

clean:
	@echo "--- 🧹 PURGANDO ENTROPÍA (Axioma Ω24) ---"
	rm -rf $(BUILD_DIR)

.PHONY: all clean init_build_dir

