# SPEC: Deconstrucción en Sala Limpia y Arquitectura Bare-Metal de ERIDU-INFER

## 1. Diagnóstico Termodinámico de la Pila Comercial (Anergía)
Las soluciones de inferencia local comerciales (LM Studio, Ollama, LocalAI) incurren en una degradación masiva de exergía por tres factores deterministas:
1. **Sobrecarga de Wrappers Web (Electron / Chromium):** Asignación de 1.5 a 2.0 GB de memoria física exclusivamente para el runtime de Node.js y renderizado Chromium.
2. **Cuello de Botella de Loopback HTTP (localhost:11434 / 1234):** En cada petición autorregresiva de streaming (SSE), el sistema fragmenta el flujo en paquetes TCP/IP, cabeceras HTTP chunked y serialización/deserialización JSON de cadenas de texto por cada token emitido.
3. **Duplicación de Páginas en Memoria ($RFO > 0$):** Inadecuada explotación de la arquitectura de memoria unificada (UMA) de Apple Silicon, copiando buffers entre memoria de CPU y memoria de GPU.

## 2. Especificación de Reconstrucción Soberana (Salto Topológico)
ERIDU-INFER sustituye la pila comercial por un microkernel en silicio:
- **Zero-HTTP IPC Channel:** Canal de comunicación inter-proceso mediante Unix Domain Sockets (`/tmp/eridu-infer.sock`) y Seqlock Single-Producer Multi-Consumer (SPMC) KUDURRU-64 alineado a línea de caché de 64 bytes (`#[repr(align(64))]`).
- **GGUF v3 Ingestion Zero-Copy:** Mapeo de archivos de modelo vía `mmap(MAP_SHARED)` con parseo little-endian en $O(1)$ de metadatos y tensores, indexando offsets sin copias intermedias en el heap.
- **Alineación de Memoria Unificada (UMA):** Bloques de tensores y pools de buffers alineados estrictamente a páginas de 16 KB (Darwin ARM64) y líneas de 128 bytes, garantizando paso de punteros directos a Metal Shaders (`MTLStorageModeShared`) con factor de copia cero ($RFO = 0$).
- **Causal Gate Ring-0 (EU AI Act Arts. 12-14):** Evaluación determinista de la 7-tupla causal previa a la ejecución, emisión de atestación criptográfica inmutable (`B60-...`) y hash WORM SHA-256 sin fuga de datos brutos.
- **Compatibilidad Dual:** Servidor HTTP/WebSocket axum embebido para clientes legacy (OpenAI REST en `:1234` y LM Studio CLI en `:41343`).

## 3. Topología de Conexión
```text
[ Cliente Agéntico / IDE ]
         │
         ├──► /tmp/eridu-infer.sock (UDS Zero-HTTP / Seqlock KUDURRU-64)
         │
         └──► http://127.0.0.1:1234 (OpenAI REST / HUD Console)
                     │
                     ▼
             [ Causal Gate Ring-0 ] ──► Ledger WORM (SHA-256 / SCITT)
                     │
                     ▼
          [ GGUF v3 Memory Map ]
                     │
                     ▼
       [ Apple Silicon UMA 16 KB Pool ] ──► Metal GPU (RFO = 0)
```
