#!/usr/bin/env bash
# CORTEX 7 Strike Packager v1.0
# Packages the 7 P0/P1 Immunefi reports into a clean submissions folder.

set -e

BASE_DIR="/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/reports"
OUT_DIR="$BASE_DIR/FINAL_7_STRIKES_MAY2026"
ZIP_NAME="$BASE_DIR/CORTEX_7_IMMUNEFI_SUBMISSIONS.zip"

echo "=== [CORTEX 7 STRIKE PACKAGER] Initializing ==="

# 1. Clean output directory
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
mkdir -p "$OUT_DIR/1_K2_Lending_Close_Factor_Bypass"
mkdir -p "$OUT_DIR/2_Exactly_Stale_Oracle"
mkdir -p "$OUT_DIR/3_Exactly_VerifiedMarket_Borrow_Bypass"
mkdir -p "$OUT_DIR/4_Exactly_VerifiedMarket_Delegate_Bypass"
mkdir -p "$OUT_DIR/5_Firedancer_Funk_State_Ghosting"
mkdir -p "$OUT_DIR/6_Lido_V3_VaultHub_Untracked_ETH"
mkdir -p "$OUT_DIR/7_LayerZero_Shadow_Exploit"

echo ">> Structure created."

# Copy files
cp "$BASE_DIR/k2-lending-close-factor-bypass-c4.md" "$OUT_DIR/1_K2_Lending_Close_Factor_Bypass/"
cp "$BASE_DIR/poc/k2-lending-close-factor-bypass-poc.rs" "$OUT_DIR/1_K2_Lending_Close_Factor_Bypass/"

cp "$BASE_DIR/exactly-stale-oracle-immunefi-submission.md" "$OUT_DIR/2_Exactly_Stale_Oracle/"

cp "$BASE_DIR/exactly-verifiedmarket-borrow-bypass-immunefi.md" "$OUT_DIR/3_Exactly_VerifiedMarket_Borrow_Bypass/"
cp "$BASE_DIR/exactly-verifiedmarket-bypass-poc.sol" "$OUT_DIR/3_Exactly_VerifiedMarket_Borrow_Bypass/"

cp "$BASE_DIR/exactly-verifiedmarket-delegate-bypass-reopened.md" "$OUT_DIR/4_Exactly_VerifiedMarket_Delegate_Bypass/"

cp "$BASE_DIR/firedancer-funk-state-ghosting-c5.md" "$OUT_DIR/5_Firedancer_Funk_State_Ghosting/"
cp "$BASE_DIR/test_ghosting_poc.c" "$OUT_DIR/5_Firedancer_Funk_State_Ghosting/"

cp "$BASE_DIR/lido-v3-vaulthub-untracked-eth-injection.md" "$OUT_DIR/6_Lido_V3_VaultHub_Untracked_ETH/"

cp "$BASE_DIR/layerzero-shadow-exploit-immunefi.md" "$OUT_DIR/7_LayerZero_Shadow_Exploit/"
cp "$BASE_DIR/layerzero-shadow-exploit-poc.sol" "$OUT_DIR/7_LayerZero_Shadow_Exploit/"

echo ">> Files copied."

# Integrity signatures
echo ">> Generating signatures..."
find "$OUT_DIR" -type f -exec shasum -a 256 {} \; > "$OUT_DIR/STRIKE_MANIFEST_SHA256.txt"

# Compress
echo ">> Compressing to: $ZIP_NAME"
cd "$BASE_DIR"
rm -f "$ZIP_NAME"
zip -r "$ZIP_NAME" "FINAL_7_STRIKES_MAY2026"

echo "=== [STRIKE READY] Bundle saved to: $ZIP_NAME ==="
