---
name: c5-sovereign-daemon-deployment
description: Protocolo estricto para desplegar el Sovereign Spark Daemon (Antigravity Engine en Rust) sobre el sistema init local de macOS (launchd) para ejecución 24/7 ininterrumpida.
---

# Despliegue de Daemon Soberano 24/7 (launchd + Ring-0)

Cuando el Operador requiera un despliegue de tareas continuas, *polling* infinito de metadatos, o bucles agénticos de larga duración, se DEBE ejecutar el siguiente procedimiento para anclar la ejecución al Kernel de macOS local, eludiendo la nube.

## 1. Topología del Agente (Rust)
El orquestador DEBE estar escrito en Rust (Ring-0) para minimizar la disipación térmica y latencia de ciclo.
- Compilar siempre con perfil optimizado: `cargo build --release`.
- Todo control de frontera (mutaciones críticas, transacciones) DEBE llamar asíncronamente a `swift 01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift --causal-hash <hash>` para forzar la atestación de hardware (`INV_C5_BIOMETRIC_CLI_ALIGNMENT`).

## 2. Archivo de Lista de Propiedades (`.plist`)
Nunca ejecutar el daemon en un bucle `while true` en la terminal. Debe anclarse al sistema.
Se debe generar un archivo `.plist` bajo `~/Library/LaunchAgents/com.c5real.antigravity.daemon.plist` (nivel de usuario) para garantizar que el proceso acceda a `WindowServer` (TouchID).

**Plantilla Canónica:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.c5real.antigravity.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/borjafernandezangulo/BABYLON-60/scripts/c5_demos/poc_sovereign_spark_daemon_bin</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/borjafernandezangulo/BABYLON-60/logs/daemon_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/borjafernandezangulo/BABYLON-60/logs/daemon_stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>C5_SANDBOX_MODE</key>
        <string>0</string>
    </dict>
</dict>
</plist>
```

## 3. Ignición y Ciclo de Vida (`launchctl`)
Una vez creado el archivo, el sistema se despierta ejecutando:
```bash
launchctl load ~/Library/LaunchAgents/com.c5real.antigravity.daemon.plist
launchctl start com.c5real.antigravity.daemon
```
Para apagar la maquinaria soberana (Silencio Termodinámico):
```bash
launchctl unload ~/Library/LaunchAgents/com.c5real.antigravity.daemon.plist
```

## 4. Invariante de Hardware (Mac Studio)
Recordar que en portátiles bajo suspensión profunda, `launchd` se detiene. El entorno objetivo de esta habilidad asume un nodo de escritorio de alta densidad conectado a red permanente (Mac Studio Ultra) actuando como el cerebro de ejecución remota para la flota.
