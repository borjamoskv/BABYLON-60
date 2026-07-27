#!/bin/bash
# [C5-REAL] Exergy-Maximized — Resource Reclamation Engine
# Prevents file descriptor locks, orphaned sub-processes, and memory leaks.

set -euo pipefail

echo "=== CORTEX: RECLAIMING SYSTEM RESOURCES ==="

# 1. Terminate orphaned sub-processes originating from Python/CORTEX runs
echo "[*] Auditing running Python processes..."
CURRENT_PID=$$
# Find pytests, uvicorns, and python runs related to this codebase (excluding this script's PID)
STALE_PIDS=$(pgrep -f "pytest|uvicorn|cortex|run_mcp_server" | grep -v "$CURRENT_PID" || true)

if [ -n "$STALE_PIDS" ]; then
    echo "[!] Found stale process PIDs: ${STALE_PIDS//$'\n'/ }"
    for PID in $STALE_PIDS; do
        if kill -0 "$PID" 2>/dev/null; then
            echo "[*] Terminating process $PID..."
            kill -15 "$PID" 2>/dev/null || true
            sleep 0.2
            # Force kill if still alive
            kill -9 "$PID" 2>/dev/null || true
        fi
    done
    echo "[+] Stale processes cleared."
else
    echo "[+] No stale CORTEX/Python processes found."
fi

# 2. Release lock and transaction logs of database files safely
echo "[*] Cleaning SQLite shared memory and WAL files..."
# Delete WAL and SHM files ONLY if no python processes are using them
if ! pgrep -f "python" >/dev/null; then
    find . -maxdepth 2 -name "*.db-wal" -exec rm -f {} +
    find . -maxdepth 2 -name "*.db-shm" -exec rm -f {} +
    echo "[+] DB temporary state files purged."
else
    echo "[!] Active Python processes detected. Skipping WAL/SHM file purge to prevent corruption."
fi

# 3. Analyze OS File Descriptor Limits
echo "[*] Auditing OS resource limits..."
CURRENT_LIMIT=$(ulimit -n)
echo "    Current Max Open Files (ulimit -n): $CURRENT_LIMIT"

if [ "$CURRENT_LIMIT" -lt 10240 ]; then
    echo "    [WARNING] Limit is too low. Recommended: >= 10240."
    echo "    To raise limits permanently on macOS, execute:"
    echo "    sudo launchctl limit maxfiles 65536 65536"
    echo "    Or add 'ulimit -n 10240' to your shell profile (~/.zshrc)."
else
    echo "    [+] Open files limits are adequate."
fi

# 4. Verify system clean status
echo "=== RECLAMATION COMPLETE ==="
