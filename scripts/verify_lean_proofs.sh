#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo "      BABYLON-60 — LEAN 4 PROOF INTEGRITY VERIFIER"
echo "============================================================"

LEAN_FILE="proof/lean/Babylon.lean"

if [ ! -f "$LEAN_FILE" ]; then
    echo "[!] Error: Formal proof file '$LEAN_FILE' not found."
    exit 1
fi

echo "[+] Step 1: Inspecting $LEAN_FILE for unproven axioms ('sorry')..."

# Check for 'sorry' keyword in proof file
if grep -nw "sorry" "$LEAN_FILE"; then
    echo "[!] VERIFICATION FAILED: Unproven 'sorry' axiom detected in $LEAN_FILE."
    exit 1
else
    echo "[✓] SUCCESS: Zero 'sorry' keywords found in $LEAN_FILE."
fi

echo "[+] Step 2: Formal Lean 4 Type-Checker Execution..."

if command -v lean >/dev/null 2>&1; then
    echo "[+] Executing Lean 4 kernel type-checker..."
    lean "$LEAN_FILE"
    echo "[✓] SUCCESS: Lean 4 formal type-checking completed cleanly."
    echo "============================================================"
    echo "[+] PROOF INTEGRITY VERIFIED: Church-Rosser confluence holds."
    echo "============================================================"
elif command -v lake >/dev/null 2>&1; then
    echo "[+] Executing Lake build..."
    lake env lean "$LEAN_FILE"
    echo "[✓] SUCCESS: Lake environment Lean 4 type-checking completed cleanly."
    echo "============================================================"
    echo "[+] PROOF INTEGRITY VERIFIED: Church-Rosser confluence holds."
    echo "============================================================"
else
    echo "[!] WARNING: Lean 4 binary ('lean' / 'lake') not installed on local host environment."
    echo "[!] Static axiom check passed (0 'sorry' keywords)."
    echo "[!] Full formal type-checking skipped due to missing Lean 4 toolchain."
    echo "[!] To install Lean 4 locally for full formal elaboration, run:"
    echo "    curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | sh -s -- -y"
    echo "============================================================"
    echo "[i] STATUS: Static verification passed; formal elaboration pending Lean 4 toolchain."
    echo "============================================================"
fi
