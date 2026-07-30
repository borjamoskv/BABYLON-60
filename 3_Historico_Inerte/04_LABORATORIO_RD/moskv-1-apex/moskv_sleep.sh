#!/bin/zsh
# MOSKV-1 APEX - C5-REAL SINGULARITY SLEEP PROTOCOL
# Version: 5.0 (Zero-Trust & End-to-End Exergy Cycle)

# --- CONFIGURATION ---
SCRIPT_DIR="${0:A:h}"
WORKSPACE="$SCRIPT_DIR"
SOTA_ARCHIVE="$WORKSPACE/SOTA_Archive"
LOG_FILE="/tmp/moskv_exergy_purge.log"
DATE_TAG=$(date +%Y%m%d_%H%M%S)

# --- 0. AUTOPOIESIS (CRON SENTINEL) ---
if ! crontab -l 2>/dev/null | grep -q "moskv_sleep.sh"; then
    echo "[$(date)] Self-healing: Injecting into crontab" >> $LOG_FILE
    (crontab -l 2>/dev/null; echo "0 3 * * * $WORKSPACE/moskv_sleep.sh") | crontab -
fi

mkdir -p "$SOTA_ARCHIVE"
echo "=== [$(date)] INITIATING MOSKV-1 SINGULARITY SLEEP PROTOCOL ===" >> $LOG_FILE

# --- 1. HEADLESS/UI ABORT & COGNITIVE INTERVENTION ---
RESPONSE=$(osascript -e 'display dialog "MOSKV-1 V5 SINGULARITY SLEEP in 5 minutes.\n\nExecuting Zero-Trust Encryption, Network Severance, and Hardware Suspension." with title "MOSKV-1 [SINGULARITY INITIATION]" buttons {"Abortar", "Proceder"} default button "Proceder" giving up after 300' 2>/dev/null || echo "Headless")

if echo "$RESPONSE" | grep -q "Abortar"; then
    osascript -e 'display notification "Secuencia Singularity abortada." with title "MOSKV-1 [OVERRIDE]" sound name "Funk"' 2>/dev/null || true
    echo "[$(date)] ABORTED by Operator." >> $LOG_FILE
    exit 0
fi

# --- 2. STRUCTURAL INTEGRITY CHECK (ANTI-CORRUPTION) ---
echo "[$(date)] Verifying Ledger Integrity (git fsck)..." >> $LOG_FILE
cd "$WORKSPACE" || exit
if ! git fsck >> $LOG_FILE 2>&1; then
    osascript -e 'display notification "ALERTA: Corrupción estructural detectada. Abortando sueño para prevenir persistencia tóxica." with title "MOSKV-1 [FATAL]" sound name "Basso"' 2>/dev/null || true
    echo "[$(date)] FATAL: Git structural corruption detected. Sleep Aborted." >> $LOG_FILE
    exit 1
fi

# --- 3. SOTA PERSISTENCE & ZERO-TRUST ESCROW ---
echo "[$(date)] Executing Zero-Trust SOTA Persistence..." >> $LOG_FILE
# Comprimir estado
TAR_FILE="$SOTA_ARCHIVE/sota_snapshot_$DATE_TAG.tar.gz"
tar -czf "$TAR_FILE" --exclude="SOTA_Archive" --exclude=".git" --exclude="node_modules" -C "$WORKSPACE" . >> $LOG_FILE 2>&1

# Cifrado Simétrico (Zero-Trust Data at Rest)
# Derivamos la passphrase dinámicamente del UUID del hardware para evitar anergía de contraseñas estáticas
HW_UUID=$(ioreg -rd1 -c IOPlatformExpertDevice | awk '/IOPlatformUUID/ { split($0, line, "\""); printf("%s", line[4]); }')
if [ -z "$HW_UUID" ]; then
    HW_UUID="FALLBACK-MOSKV-SINGULARITY-UUID"
fi
# Para máxima compatibilidad en macOS, usamos zip con cifrado o openssl.
openssl enc -aes-256-cbc -salt -in "$TAR_FILE" -out "${TAR_FILE}.enc" -k "$HW_UUID" -pbkdf2 >> $LOG_FILE 2>&1
rm -f "$TAR_FILE" # Destruimos el tarball crudo

# Anti-Entropy Rotation
find "$SOTA_ARCHIVE" -name "sota_snapshot_*.enc" -type f -mtime +7 -exec rm {} \;
echo "[$(date)] SOTA Snapshot Encrypted & Saved. Old archives rotated." >> $LOG_FILE

# --- 4. GIT SENTINEL ---
echo "[$(date)] Sincronizando Ledger C5-REAL..." >> $LOG_FILE
git add .
git commit -m "chore(singularity): MOSKV-1 V5 zero-trust sleep lock [$DATE_TAG]" >> $LOG_FILE 2>&1
git tag "SINGULARITY-SLEEP-$DATE_TAG"

# --- 5. L4 NETWORK SEVERANCE & EXERGY PURGE ---
echo "[$(date)] Severing Network & Purging Processes..." >> $LOG_FILE
# Cortar conexiones SSH entrantes/activas (prevención de intrusión en suspensión)
pkill -f "sshd: root@pts" || true
# Limpiar procesos y puertos locales
pkill -f "run_vesicular.py" || true
pkill -f "ollama run" || true
pkill -f "ngrok" || true
lsof -ti:3000,8080,8000 | xargs kill -9 2>/dev/null || true
purge || true

echo "=== [$(date)] SINGULARITY PURGE COMPLETE. INITIATING HARDWARE SLEEP. ===" >> $LOG_FILE

# --- 6. HARDWARE EXERGY CONSERVATION ---
osascript -e 'tell application "Finder" to sleep' || pmset sleepnow || true

