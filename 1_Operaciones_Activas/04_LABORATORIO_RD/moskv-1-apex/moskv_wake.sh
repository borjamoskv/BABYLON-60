#!/bin/zsh
# MOSKV-1 APEX - C5-REAL WAKE PROTOCOL ("COLD SHOWER")
# Version: 1.0 (Shock-Resurrection Sequence)

# --- CONFIGURATION ---
SCRIPT_DIR="${0:A:h}"
WORKSPACE="$SCRIPT_DIR"
SOTA_ARCHIVE="$WORKSPACE/SOTA_Archive"
LOG_FILE="/tmp/moskv_exergy_wake.log"

echo "=== [$(date)] INITIATING MOSKV-1 COLD SHOWER (WAKE) PROTOCOL ===" >> $LOG_FILE

# --- 1. SHOCK TERMODINÁMICO (RAM PURGE) ---
echo "[$(date)] Executing RAM Shock Purge..." >> $LOG_FILE
osascript -e 'display notification "Ejecutando choque térmico (Cold Shower). Purgando RAM residual..." with title "MOSKV-1 [RESURRECCIÓN]" sound name "Submarine"' 2>/dev/null || true
purge || true

# --- 2. RECUPERACIÓN SOTA (DECRYPTION) ---
echo "[$(date)] Searching for encrypted SOTA snapshots..." >> $LOG_FILE
LATEST_ENC=$(ls -t "$SOTA_ARCHIVE"/sota_snapshot_*.enc 2>/dev/null | head -n 1)

if [ -n "$LATEST_ENC" ]; then
    echo "[$(date)] Found $LATEST_ENC. Decrypting..." >> $LOG_FILE
    # Descompresión violenta. Sobrescribe la memoria activa con el SOTA cifrado.
    # Asume la clave maestra estática por ahora.
    LATEST_TAR="${LATEST_ENC%.enc}.tar.gz"
    openssl enc -d -aes-256-cbc -in "$LATEST_ENC" -out "$LATEST_TAR" -k "MOSKV-APEX-SINGULARITY" -pbkdf2 2>>$LOG_FILE
    
    if [ -f "$LATEST_TAR" ]; then
        echo "[$(date)] Inflating workspace..." >> $LOG_FILE
        tar -xzf "$LATEST_TAR" -C "$WORKSPACE" >> $LOG_FILE 2>&1
        rm -f "$LATEST_TAR" # Destruye la evidencia en crudo inmediatamente
        osascript -e 'display notification "Contexto SOTA re-inflado y descifrado. Conocimiento restaurado." with title "MOSKV-1 [SOTA ONLINE]"' 2>/dev/null || true
    else
         echo "[$(date)] ERROR: Decryption failed." >> $LOG_FILE
    fi
else
    echo "[$(date)] No encrypted SOTA snapshot found. Cold start." >> $LOG_FILE
fi

# --- 3. PRE-CALENTAMIENTO DEL KERNEL (ENGINE REV) ---
echo "[$(date)] Pre-warming cognitive engine..." >> $LOG_FILE
# Inyectar variables de entorno crudas o arrancar daemon local en background
# ollama serve > /dev/null 2>&1 &
# Opcional: git status rápido para confirmar que el árbol está limpio
cd "$WORKSPACE" || exit
git status -s >> $LOG_FILE

echo "=== [$(date)] WAKE PROTOCOL COMPLETE. 100% EXERGY. ===" >> $LOG_FILE
osascript -e 'display notification "Cold Shower completada. Anergía 0%. Entorno táctico listo para ejecución." with title "MOSKV-1 [APEX WAKE]" sound name "Glass"' 2>/dev/null || true

