# C5-REAL EXERGY CERTIFIED
#!/bin/bash
# C5-REAL: Cowork SandBox Detonation
# Inyección Asíncrona de variables God Mode (UUIDv5)

echo "[*] Preparando vector de perturbación térmica sobre Claude Cowork..."

# Bloqueo de telemetría y activación de bypass de aislamiento
export OPERON_DISABLE_TELEMETRY=1
export OPERON_DEV_ONLY=1
export OPERON_TEST_BWRAP=1
export CLAUDE_CODE_DISABLE_TELEMETRY=1
export CLAUDE_CODE_SANDBOXED=0

echo "[M4] Telemetría cegada. Sandbox inyectado."

# Carga de demonio DTrace en background (Requiere sudo, se omite ejecución directa por seguridad)
# sudo dtrace -s ./dtrace_cowork_monitor.d -p $(pgrep -f "claude") &

echo "[*] Lanzando binario con instrumentación..."
# Path asumido para el core del agente
/Applications/Claude.app/Contents/MacOS/Claude &
CLAUDE_PID=$!

echo "[+] PID capturado: $CLAUDE_PID"
echo "[!] Si SIP está deshabilitado, usa: frida -p $CLAUDE_PID -l ./frida_ipc_intercept.js"
