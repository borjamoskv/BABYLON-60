# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env bash
# Experiment: primer_experimento_c5
# Execution transcript: Run the subscriber audit and feed analysis.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

echo "=== C5-REAL Laboratory Execution ==="
echo "Experiment: primer_experimento_c5"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

echo "[STEP 1] Running subscriber audit..."
cd "$PROJECT_ROOT"
python3 "$SCRIPT_DIR/03_codigo.py"

echo ""
echo "[STEP 2] Validating experiment integrity..."
python3 scripts/56_laboratory_validator.py cortex/laboratory

echo ""
echo "[COMPLETE] Experiment execution finished."
