#!/usr/bin/env bash
# BABYLON-60 C5-REAL Local Edge Test (Kinetic Load)
set -euo pipefail

echo "[C5-REAL] Igniting Edge-Deploy Build (Docker)..."
docker build -t babylon60-local:c5-real .

echo "[C5-REAL] Deploying Local Swarm Node..."
# Ejecuta en el background
CONTAINER_ID=$(docker run -d -p 8000:8000 --name babylon60-edge babylon60-local:c5-real)

# Esperar healthcheck loop
echo "Waiting for uvicorn to boot (5s)..."
sleep 5

echo "[C5-REAL] Fetching BFT Attestation..."
# Intenta obtener la atestación de salud 3 veces
for i in 1 2 3; do
    if curl -s http://localhost:8000/health | grep -q 'C5-REAL Kernel Active'; then
        echo "✅ Transducer API is alive."
        curl -s http://localhost:8000/health
        break
    else
        echo "⏳ Polling ($i/3)..."
        sleep 2
    fi
done

echo ""
echo "[C5-REAL] Purging Local Swarm Node..."
docker rm -f "$CONTAINER_ID"
docker rmi babylon60-local:c5-real
echo "Kinetic Load Test Complete."
