# ERIDU-INFER · Sovereign Air-Gapped Local Inference Engine

Motor de inferencia soberana local bare-metal y adaptador de protocolos en Apple Silicon (Darwin ARM64). Erradica la anergía de los envoltorios comerciales (bloat de Electron, latencias de loopback HTTP e IPC ineficiente) mediante primitives en silicio puro.

## Características Principales
- **Zero-HTTP IPC:** Canal Unix Domain Socket (`/tmp/eridu-infer.sock`) y Seqlock SPMC KUDURRU-64 (64 bytes cache-line aligned) para comunicación inter-agente a velocidad de memoria unificada.
- **Apple Silicon UMA Zero-Copy ($RFO = 0$):** Asignación alineada a páginas de 16 KB y líneas de 128 bytes para paso directo a shaders Metal sin duplicación de memoria.
- **Parser GGUF v3 en $O(1)$:** Deserialización zero-copy sobre archivos mapeados en memoria (`mmap`).
- **Causal Gate & SCITT Ledger (EU AI Act Arts. 12-14):** Atestación criptográfica determinista con recibos SHA-256 (`B60-...`).
- **Compatibilidad Dual:** Compatible con la API de OpenAI (`/v1/chat/completions`) y el CLI de LM Studio (`GET /lms-status`).
- **Web HUD Autónomo:** Consola de monitoreo servida desde una constante binaria embebida en `/` y `/hud`.

## Compilación y Pruebas
```bash
cargo check
cargo test
cargo run --release
```

## Gestión del Demonio launchd en macOS
```bash
# Instalar y activar demonio permanente
eridu-infer --install-daemon

# Comprobar estado del servicio
eridu-infer --status

# Desinstalar y purgar plist
eridu-infer --uninstall-daemon
```
