#!/bin/bash
set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

echo "Building Soroban contracts..."
echo ""

# List of contract directories to build
contracts=(
    "kinetic-router"
    "a-token"
    "debt-token"
    "price-oracle"
    "pool-configurator"
    "liquidation-engine"
    "interest-rate-strategy"
    "incentives"
    "treasury"
    "flash-liquidation-helper"
    "token"
    "aquarius-swap-adapter"
    "soroswap-swap-adapter"
    # "redstone-adapter"  # Only needed for testnet (RedStone maintains mainnet adapter)
    # "redstone-feed-wrapper"  # Removed from workspace; build separately if needed
)

# Build each contract using stellar contract build
for contract in "${contracts[@]}"; do
    echo "Building $contract..."
    (cd "contracts/$contract" && stellar contract build)
done

echo ""
echo "Optimizing WASM files..."
echo ""

# Optimize all WASM files
# Note: `stellar contract optimize` is deprecated in newer CLI versions.
# We try the old command and fall back gracefully.
optimized_count=0
for wasm in target/wasm32v1-none/release/*.wasm; do
    if [ -f "$wasm" ] && [ -s "$wasm" ] && [[ ! "$wasm" =~ \.optimized\.wasm$ ]]; then
        echo "Optimizing $(basename $wasm)..."
        rm -f "${wasm%.wasm}.optimized.wasm"
        stellar contract optimize --wasm "$wasm" --wasm-out "${wasm%.wasm}.optimized.wasm" || true
        optimized_count=$((optimized_count + 1))
    fi
done

if [ $optimized_count -eq 0 ]; then
    echo "No WASM files to optimize."
fi

echo ""
echo "Build complete. Optimized WASMs are in target/wasm32v1-none/release/"
echo ""
echo "Contract sizes:"
if ls target/wasm32v1-none/release/*.optimized.wasm 1> /dev/null 2>&1; then
    ls -lh target/wasm32v1-none/release/*.optimized.wasm | awk '{print "  " $9 ": " $5}'
else
    echo "  No optimized WASM files found."
fi
