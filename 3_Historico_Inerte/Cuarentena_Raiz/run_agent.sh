# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env bash
# run_agent.sh — Single Zero-Trust Entrypoint for Kernel Operations
# Pipeline: detect_sim.py -> runtime_wrapper.py -> verify_receipt.py

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

# 1. Pre-Execution Gate: Scan plan for synthetic artifacts or unbacked claims
echo "[run_agent.sh] Step 1: scanning plan via detect_sim.py..." | tee -a "${LOG}"
python3 scripts/detect_sim.py "${PLAN}" --strict 2>&1 | tee -a "${LOG}"
DETECT_EXIT="${PIPESTATUS[0]}"

if [ "${DETECT_EXIT}" -ne 0 ]; then
  echo "[ABORT] Synthetic artifacts or unbacked claims detected in plan." | tee -a "${LOG}"
  exit 3
fi

# 2. Execution Phase: Run runtime_wrapper.py
echo "[run_agent.sh] Step 2: executing plan via runtime_wrapper.py..." | tee -a "${LOG}"
python3 scripts/runtime_wrapper.py "${PLAN}" --outdir "${RECEIPTS_DIR}" 2>&1 | tee -a "${LOG}"
WRAPPER_EXIT="${PIPESTATUS[0]}"

if [ "${WRAPPER_EXIT}" -ne 0 ]; then
  echo "[ABORT] runtime_wrapper failed (rc=${WRAPPER_EXIT})." | tee -a "${LOG}"
  exit "${WRAPPER_EXIT}"
fi

# 3. Verification Phase: Verify receipt vs disk state
RECEIPT=$(ls -t "${RECEIPTS_DIR}"/run-*.json 2>/dev/null | head -1)
echo "[run_agent.sh] Step 3: verifying receipt ${RECEIPT} via verify_receipt.py..." | tee -a "${LOG}"
python3 scripts/verify_receipt.py "${RECEIPT}" 2>&1 | tee -a "${LOG}"
VERIFIER_EXIT="${PIPESTATUS[0]}"

if [ "${VERIFIER_EXIT}" -ne 0 ]; then
  echo "[ABORT] verify_receipt failed (rc=${VERIFIER_EXIT})." | tee -a "${LOG}"
  exit "${VERIFIER_EXIT}"
fi

echo "=== ZERO TRUST PIPELINE: PASS ===" | tee -a "${LOG}"
exit 0
