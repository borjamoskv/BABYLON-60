# ERIDU-INFER · Local Inference Adapter & IPC Daemon (`crates/eridu-infer/`)

Adaptador experimental de inferencia local en espacio de usuario (`EL0`, Darwin ARM64) y pasarela de protocolos HTTP/Unix Domain Socket. *(Nota: este crate es un adaptador auxiliar de inferencia local y no forma parte del TCB verificado en [`CLAIMS.toml`](../../CLAIMS.toml)).*

## Características Principales (`src/`)
- **IPC por Unix Domain Socket (`ipc.rs`):** Canal `/tmp/eridu-infer.sock` y estructura `SharedManifest` de 64 bytes (`align(64)`) en espacio de usuario.
- **Asignación Alineada a 16 KB (`uma.rs`):** Buffers en espacio de usuario alineados a páginas de 16 KB y líneas de 128 bytes en Apple Silicon *(el tráfico de coherencia RFO y el acoplamiento directo a shaders Metal permanecen como objetivos de diseño no verificados en `CLAIMS.toml`)*.
- **Parser de Cabeceras GGUF v3 (`gguf.rs`):** Lectura de metadatos GGUF v3 sobre archivos locales.
- **Gate Local de Recibos (`gate.rs`, `auth.rs`):** Emisión de recibos locales con digest `SHA-256` (`B60-...`) para trazabilidad de peticiones *(distinto de los recibos normativos `COSE_Sign1` Ed25519 RFC 9942 de `src/receipt.rs`)*.
- **Compatibilidad Dual (`server.rs`):** Endpoints compatibles con OpenAI (`/v1/chat/completions`) y estado local (`GET /lms-status`).
- **Web HUD (`hud.rs`):** Consola ligera servida en `/` y `/hud`.

## Compilación y Pruebas
```bash
cargo check -q --locked -p eridu-infer
cargo test --locked -p eridu-infer
cargo run --locked --release -p eridu-infer
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
