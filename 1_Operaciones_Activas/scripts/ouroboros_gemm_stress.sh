# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env bash
# Ouroboros GEMM continuous stress benchmark
# Runs the GEMM stress test repeatedly, logging timestamps and performance.
# Ultralight loop for long‑running thermodynamic analysis on Apple M3 Pro.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/69_gemm_stress_test.py"

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
  echo "[ERROR] Stress test script not found at $PYTHON_SCRIPT"
  exit 1
fi

echo "--- Ouroboros GEMM Stress Benchmark started ---"
while true; do
  TS=$(date '+%Y-%m-%d %H:%M:%S')
  echo "\n--- $TS ---"
  # Run the stress test (it rebuilds the library and executes the benchmark)
  python3 "$PYTHON_SCRIPT"
  # Optional short pause to avoid overwhelming the scheduler (adjust as needed)
  sleep 0.5
done
