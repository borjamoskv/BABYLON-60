#!/bin/bash
set -e

# Read deployment config
KINETIC_ROUTER="CBEHLQTFRCMAKIUGSQ5CGALJPMXVB5KYNGDSXRALX2M2MDFROWE4O6JH"
RPC_URL="https://soroban-testnet.stellar.org"
NETWORK_PASSPHRASE="Test SDF Network ; September 2015"
OUTPUT_DIR="./money-market-frontend/src/contracts-client"

echo "Generating TypeScript bindings from deployed contracts..."
echo "Kinetic Router: $KINETIC_ROUTER"
echo ""

# Generate bindings from deployed contract
stellar contract bindings typescript \
  --contract-id "$KINETIC_ROUTER" \
  --rpc-url "$RPC_URL" \
  --network-passphrase "$NETWORK_PASSPHRASE" \
  --output-dir "$OUTPUT_DIR" \
  --overwrite

echo ""
echo "Bindings generated at $OUTPUT_DIR"
echo "Installing dependencies..."
echo ""

cd "$OUTPUT_DIR"
npm install
npm run build

echo ""
echo "Client bindings ready."
echo ""
echo "Next steps:"
echo "1. Update imports in frontend to use local bindings instead of @shapeshifter-technologies/k2-contracts-client"
echo "2. Import from '~/contracts-client' instead"
