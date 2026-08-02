# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env bash
set -euo pipefail

# Descargar los certificados de FreeTSA si no existen
if [ ! -f "cacert.pem" ]; then
    echo "[*] Descargando CA certificate de FreeTSA..."
    curl -s -o cacert.pem https://freetsa.org/files/cacert.pem
fi

if [ ! -f "tsa.crt" ]; then
    echo "[*] Descargando TSA certificate de FreeTSA..."
    curl -s -o tsa.crt https://freetsa.org/files/tsa.crt
fi

# Hacer el commit criptográfico. Si falla, el script se detiene (gracias a -e)
echo "[*] Ejecutando git commit -S..."
git commit -S -m "$1"

# Extraer el hash del commit resultante
COMMIT_HASH=$(git rev-parse HEAD)
echo "[*] Commit anclado: $COMMIT_HASH"

HASH_FILE=".cortex_utbh/commit_${COMMIT_HASH}.hash"
TSQ_FILE=".cortex_utbh/commit_${COMMIT_HASH}.tsq"
TSR_FILE=".cortex_utbh/commit_${COMMIT_HASH}.tsr"

echo "Sello Criptográfico C5-REAL para Commit: $COMMIT_HASH" > "$HASH_FILE"

# Generar el query (CON NONCE, resolviendo el problema de replay)
echo "[*] Generando Time Stamp Query..."
openssl ts -query -data "$HASH_FILE" -cert -sha256 > "$TSQ_FILE"

# Llamar al TSA
echo "[*] Solicitando sello a freetsa.org..."
curl -s -H "Content-Type: application/timestamp-query" --data-binary "@${TSQ_FILE}" http://freetsa.org/tsr > "$TSR_FILE"

# VERIFICACIÓN REAL (No solo parseo)
echo "[*] Ejecutando VERIFICACIÓN CRIPTOGRÁFICA (QTSP)..."
openssl ts -verify -in "$TSR_FILE" -queryfile "$TSQ_FILE" -CAfile cacert.pem -untrusted tsa.crt

echo "[OK] Cadena atestada y verificada matemáticamente. Fail-Stop superado."
