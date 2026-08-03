#!/usr/bin/env bash
# El Bucle Termodinámico Eterno
echo "[*] Iniciando el Bucle de Supervivencia B60..."

while [ ! -f "out/video.mp4" ]; do
    echo "[+] Ejecutando render_chunks.py..."
    python3 render_chunks.py
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[*] Renderizado completado con éxito."
        break
    else
        echo "[-] V8 ha reventado. El Bucle absorberá la entropía y reanudará en 3 segundos..."
        sleep 3
        # Matar zombis por si acaso
        pkill -f Chrome || true
    fi
done
