# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env bash
set -e

# MOSKV-1 APEX KERNEL: C5-REAL Cloudflare Purge Script
# Purges Cloudflare edge cache for the configured Zone ID.

echo "▸ Iniciando purga de caché en Cloudflare..."

# Load .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "$CLOUDFLARE_ZONE_ID" ] || [ -z "$CLOUDFLARE_API_TOKEN" ]; then
  echo "❌ Error: CLOUDFLARE_ZONE_ID o CLOUDFLARE_API_TOKEN no definidos en el entorno (.env)."
  echo "   Obtén las credenciales en el dashboard de Cloudflare."
  exit 1
fi

RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$CLOUDFLARE_ZONE_ID/purge_cache" \
     -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
     -H "Content-Type: application/json" \
     --data '{"purge_everything":true}')

SUCCESS=$(echo $RESPONSE | grep -o '"success":true' || true)

if [ -n "$SUCCESS" ]; then
  echo "✓ PURGE SUCCESS: Caché de Cloudflare purgada exitosamente."
else
  echo "❌ PURGE FAILED: Error al purgar la caché."
  echo "Detalle de respuesta:"
  echo "$RESPONSE"
  exit 1
fi
