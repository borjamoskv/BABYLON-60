#!/usr/bin/env bash
# CORTEX Strike Packager v1.0
# Aggregates the 4 P0/P1 Immunefi reports into a single submission bundle.

set -e

BASE_DIR="/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/reports"
OUT_DIR="$BASE_DIR/FINAL_STRIKE_MAY2026"
ZIP_NAME="$BASE_DIR/CORTEX_IMMUNEFI_SUBMISSIONS.zip"

echo "=== [CORTEX STRIKE PACKAGER] Initializing ==="

# 1. Clean output directory
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
mkdir -p "$OUT_DIR/K2_Lending"
mkdir -p "$OUT_DIR/Exactly_Protocol"
mkdir -p "$OUT_DIR/Firedancer"
mkdir -p "$OUT_DIR/Lido_V3"

echo ">> Directories created."

# 2. Copy K2 Lending Artifacts (7 Vectors)
echo ">> Packaging K2 Lending Strike (7 Vectors)..."
K2_FILES=(
    "k2-lending-close-factor-bypass-c5-real.md"
    "k2-close-factor-desync-h02.md"
    "k2-flash-loan-reentrancy-h03.md"
    "k2-oracle-cache-poisoning-h01.md"
    "k2-swap-stale-interest-rate-m01.md"
    "k2-atoken-transfer-race-m02.md"
    "k2-bad-debt-unbounded-m03.md"
)

for file in "${K2_FILES[@]}"; do
    if [ -f "$BASE_DIR/$file" ]; then
        cp "$BASE_DIR/$file" "$OUT_DIR/K2_Lending/"
    else
        echo "[!] Warning: $file not found!"
    fi
done

# Copy K2 PoCs if they exist
cp "$BASE_DIR/poc/k2-lending-close-factor-bypass-poc.rs" "$OUT_DIR/K2_Lending/" || echo "Missing K2 Critical PoC"

# 3. Copy Exactly Protocol Artifacts
if [ -f "$BASE_DIR/exactly-stale-oracle-l2-immunefi.md" ]; then
    cp "$BASE_DIR/exactly-stale-oracle-l2-immunefi.md" "$OUT_DIR/Exactly_Protocol/"
    cp "$BASE_DIR/exactly-verifiedmarket-borrow-bypass-immunefi.md" "$OUT_DIR/Exactly_Protocol/" || echo "Missing Exactly Borrow Bypass"
    cp "$BASE_DIR/exactly-verifiedmarket-bypass-poc.sol" "$OUT_DIR/Exactly_Protocol/" || echo "Missing Exactly PoC"
else
    echo "[!] Exactly Protocol report not found!"
fi

# 4. Copy Firedancer Artifacts
if [ -f "$BASE_DIR/firedancer-funk-state-ghosting-c5.md" ]; then
    cp "$BASE_DIR/firedancer-funk-state-ghosting-c5.md" "$OUT_DIR/Firedancer/"
    cp "$BASE_DIR/firedancer-vm-region-oob-bypass-poc.c" "$OUT_DIR/Firedancer/" || echo "Missing Firedancer PoC"
else
    echo "[!] Firedancer report not found!"
fi

# 5. Copy Lido V3 Artifacts
if [ -f "$BASE_DIR/lido-v3-vaulthub-untracked-eth-injection.md" ]; then
    cp "$BASE_DIR/lido-v3-vaulthub-untracked-eth-injection.md" "$OUT_DIR/Lido_V3/"
else
    echo "[!] Lido V3 report not found!"
fi

echo ">> Artifacts copied successfully."

# 6. Generate Ledger Signature
echo ">> Generating SHA-256 integrity signatures..."
find "$OUT_DIR" -type f -exec shasum -a 256 {} \; > "$OUT_DIR/STRIKE_MANIFEST_SHA256.txt"

# 7. Compress
echo ">> Compressing bundle..."
cd "$BASE_DIR"
rm -f "$ZIP_NAME"
zip -r "$ZIP_NAME" "FINAL_STRIKE_MAY2026"

echo "=== [STRIKE READY] Bundle saved to: $ZIP_NAME ==="
