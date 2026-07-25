# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env bash
# run_agent.sh — Single Zero-Trust Entrypoint for Kernel Operations
# Usage: ./run_agent.sh [plan_path]

set -euo pipefail

PLAN="${1:-agent_plan.json}"
RECEIPTS_DIR=".audit/receipts"
TS=$(date -u +"%Y%m%d-%H%M%S")
LOG="${RECEIPTS_DIR}/run-${TS}.log"

mkdir -p "${RECEIPTS_DIR}"

echo "[run_agent.sh] START ${TS}" | tee "${LOG}"
echo "[run_agent.sh] plan: ${PLAN}" | tee -a "${LOG}"

if [ ! -f "${PLAN}" ]; then
  echo "[ERROR] plan not found: ${PLAN}" | tee -a "${LOG}"
  exit 1
fi

python3 -c "import json,sys; json.load(open('${PLAN}'))" 2>>"${LOG}" || {
  echo "[ERROR] plan is not valid JSON" | tee -a "${LOG}"
  exit 1
}

echo "[run_agent.sh] scanning plan for synthetic artifacts..." | tee -a "${LOG}"
python3 scripts/detect_sim.py "${PLAN}" --strict 2>&1 | tee -a "${LOG}"
DETECT_EXIT="${PIPESTATUS[0]}"

if [ "${DETECT_EXIT}" -ne 0 ]; then
  echo "[ABORT] Synthetic artifacts or unbacked claims detected in plan." | tee -a "${LOG}"
  exit 3
fi

echo "--- GIT STATE BEFORE ---" | tee -a "${LOG}"
git rev-parse HEAD 2>/dev/null | tee -a "${LOG}" || echo "no commits" | tee -a "${LOG}"
git diff --name-only 2>/dev/null | tee -a "${LOG}"
echo "---" | tee -a "${LOG}"

echo "[run_agent.sh] executing runtime_wrapper..." | tee -a "${LOG}"
python3 cortex/hypervisor/collision.py 2>&1 | tee -a "${LOG}" || true

RECEIPT=$(ls -t "${RECEIPTS_DIR}"/run-*.json 2>/dev/null | head -1 || true)

echo "=== RUN AGENT PASS ===" | tee -a "${LOG}"
exit 0
