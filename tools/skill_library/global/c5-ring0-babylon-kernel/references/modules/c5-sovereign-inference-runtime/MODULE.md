---
name: c5-sovereign-inference-runtime
display_name: Motor Soberano de Inferencia y Adaptador LM Studio C5-REAL
description: 'Despliegue y auditoría de motores de inferencia local bare-metal. Dispara con "eridu-infer", "inferencia soberana", "appliance ia", "lm studio protocolo", "motor inferencia local", "air-gapped infer", "servidor openai local rust", "sovereign inference runtime", "desplegar eridu-infer", "tríada jurídica".'

role: ejecutor
allowed_roles:
- ejecutor
directives:
  worktree_mode: read-write
  phase: implementation
  handoff:
    upstream: arquitecto
    downstream: auditor
---

# C5-REAL Sovereign Inference Runtime Protocol (Nivel Omega)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `ejecutor` (Implementación & Despliegue Bare-Metal)
> - **Modo de Acceso a Worktree:** `read-write` (Mutación atómica de código, binarios y configuraciones)
> - **Fase Causal:** `implementation`
> - **Contrato Handoff:** Recibe de `arquitecto` $\to$ Despacha a `auditor`

Este protocolo rige la arquitectura, compilación y despliegue de **appliances de inferencia soberana local (air-gapped)** sobre Apple Silicon, erradicando el bloat de Electron/Python mediante kernels compactos en Rust (`eridu-infer`) y blindando la privacidad bajo el marco del EU AI Act.

---

## 1. Protocolo de Ingeniería Inversa y Compatibilidad LM Studio
Al interactuar o emular la pila de LM Studio:
- **Descubrimiento de Socket:** El CLI `lms` sondea los puertos candidatos `[41343, 52993, 16141, 39414, 22931]` enviando `GET /lms-status` esperando `{"package": string, "version": string}`.
- **Payload Bun Mach-O:** El ejecutable `~/.lmstudio/bin/lms` contiene el código en la sección `__bun` del segmento `__BUN`. Se inspecciona con `otool -l` y `dd`.
- **Canales WebSocket (`lms_communication`):** Mensajes tipados (`channelCreate`, `channelSend`, `rpcCall`, `rpcResult`).
- **Autenticación Dual:** Sal estática `"Var6lhhZGAUOowV+6cOrFc1H"` concatenada con token dinámico en `~/.lmstudio/.internal/lms-key-2`.

---

## 2. Arquitectura de Silicio de `eridu-infer`
Todo motor soberano de inferencia en BABYLON-60 debe cumplir:
1. **Binario Único Bare-Metal:** Compilado en Rust con Tokio y Axum, con tamaño $< 2\text{ MB}$ y consumo en reposo $< 10\text{ MB}$ de RAM.
2. **Enlace Dual de Puertos:**
   - Puerto `41343`: Compatible con handshake y sondeo del CLI de LM Studio.
   - Puerto `1234`: Compatible con la API estándar de OpenAI (`/v1/chat/completions`, `/v1/models`).
3. **Consola Web HUD Autónoma:** Servida en `/` y `/hud` desde una constante HTML embebida (`HUD_HTML`). Cero dependencias de Node, CDN o internet exterior.
4. **Daemon Launchd en macOS:**
   - Plist en `~/Library/LaunchAgents/com.babylon60.eridu-infer.plist`.
   - Modos CLI: `--install-daemon`, `--uninstall-daemon`, `--status`.
   - Logs en `~/.babylon60/logs/`.

---

## 3. Topología de Memoria Unificada (UMA) sin Swap
Para garantizar latencias sub-segundo sin desbordamiento a disco SSD:
- **Regla del 50% de UMA:** La suma de los pesos de los modelos cuantizados no debe exceder el 50-60% de la memoria física disponible para reservar el resto a KV-Cache de contexto largo:
  - Sistema 1 (LAYA / ModernBERT): $\approx 0.3\text{ GB}$ (FP16).
  - Embeddings (BGE-M3): $\approx 2.1\text{ GB}$ (FP16).
  - Reranker (BGE-Reranker-v2): $\approx 1.2\text{ GB}$ (Q8_0).
  - Razonador (DeepSeek-R1 Distill 32B): $\approx 19.4\text{ GB}$ (Q4_K_M).
  - Redactor (Llama 3.3 70B Instruct): $\approx 38.2\text{ GB}$ (Q4_K_M).
  - **Total Confinado:** $61.2\text{ GB}$ en hardware Mac Studio de 128 GB.

---

## 4. Gobernanza Causal y Cumplimiento EU AI Act (Arts. 9-15)
- **Causal Gate Ring-0:** Intercepta la petición antes de que toque la GPU.
- **Hash WORM:** Deriva SHA-256 del contenido del prompt, modelo y timestamp.
- **Recibo SCITT:** Emite un identificador de atestación determinista (`B60-...`) grabado en SQLite WAL local.
- **Certificación Legal:** Demuestra formalmente ante AEPD/AESIA la ausencia de transmisión externa y la inmutabilidad del procesamiento local.

---

## 5. Canal IPC Zero-HTTP & Seqlock SPMC KUDURRU-64
Para eliminar la latencia de loopback TCP/IP (`localhost`) y la sobrecarga de serialización JSON en streaming:
- **Unix Domain Socket:** Listener en `/tmp/eridu-infer.sock` para comunicación inter-agente de latencia sub-milisegundo.
- **Seqlock SPMC Cache-Aligned:** Estructura `KudurruSeqlock<T>` alineada a 64 bytes (`#[repr(align(64))]`):
  - **Escritor único:** Incremento a secuencia impar durante la mutación, publicación con `Ordering::Release` a secuencia par.
  - **Múltiples lectores concurrentes:** Lectura optimista lock-free validando $s_{\text{pre}} == s_{\text{post}} \land s_{\text{pre}} \equiv 0 \pmod 2$.
  - **Prueba en Silicio:** Certificada formalmente libre de *torn reads* mediante reflexión en Lean 4 (`by decide`).

---

## 6. Ingestión GGUF v3 Zero-Copy y Asignación UMA a 16 KB
El motor ingesta modelos sin copiarlos a la memoria dinámica del heap:
- **Mmap Directo:** Mapeo de archivos GGUF v3 vía `memmap2::Mmap` con validación de magic `0x46554747` ("GGUF" en LE).
- **Offsets Alineados:** Indexación en $O(1)$ de metadatos KV y cálculo de offsets alineados al bloque `general.alignment` (32 bytes por omisión).
- **Alineación Darwin ARM64:** Todo buffer UMA (`UmaAlignedBuffer`) se pagina estrictamente a múltiplos de 16.384 bytes (`DARWIN_PAGE_SIZE = 16384`) y líneas de 128 bytes (`M_SERIES_CACHE_LINE = 128`), permitiendo paso directo a `MTLBuffer` (`MTLStorageModeShared`) con factor $RFO = 0$.

---

## 7. Repositorio Canónico y Comandos de Silicio
- **Ruta del Repositorio:** `~/10_PROJECTS/eridu-infer/`
- **Verificación Determinista:**
  ```bash
  cd ~/10_PROJECTS/eridu-infer
  cargo check
  cargo test
  cargo run --release
  ```
- **Gestión del Demonio macOS:**
  ```bash
  eridu-infer --install-daemon   # Carga plist en ~/Library/LaunchAgents/com.babylon60.eridu-infer.plist
  eridu-infer --status           # Comprueba salud en puertos 41343 y 1234
  eridu-infer --uninstall-daemon # Descarga y elimina plist
  ```

---

## 8. Arquitectura Comercial de Appliance On-Premise & M&A Exit

### 8.1. Unit Economics y Tiers de Silicio
El motor `eridu-infer` se empaqueta y monetiza como un appliance físico llave en mano (*Turnkey Appliance*):
- **Tier 1: BABYLON-MINI (Mac Mini M4 Pro 64 GB / 1 TB SSD / 10GbE):**
  - COGS (Hardware Apple + Cat6A blindado + USB Restore): ~2.680 €.
  - PVP B2B: 14.500 € (o 15.000 $).
  - Margen Bruto: 11.820 € (81,5%).
  - Comisión Comercial (15% del margen): ~1.770 €.
  - Coste Legal Unitario: 0 € (plantilla amortizada en venta #1).
  - **Margen Neto Limpio (Borja): ~10.050 € por caja**.
- **Tier 2: BABYLON-STUDIO (Mac Studio 128 GB UMA / 2 TB SSD):**
  - COGS: ~5.120 € | PVP: 24.500 € | Margen Neto Borja: ~16.480 €.
- **Ingresos Recurrentes (SLA Mantenimiento Año 2+):** 2.400 € a 3.600 € / año (>95% margen).

### 8.2. Dinámica de Tesorería de Riesgo Cero (Política 50/50)
- Prohibición absoluta de comprar hardware sin contrato firmado.
- El cliente transfiere el 50% de anticipo al firmar (7.250 € / 12.250 €), cubriendo el 100% de la compra física en Apple Store. La tesorería permanece en positivo desde $t=0$. El 50% restante se cobra tras la entrega y conexión al conmutador LAN.

### 8.3. Aprovisionamiento Zero-Touch en Silicio (`setup_appliance.sh`)
- Automatizado en `10_PROJECTS/eridu-infer/scripts/setup_appliance.sh`:
  - `pmset -a sleep 0 womp 1 autorestart 1` y `systemsetup -setrestartfreeze on` para auto-arranque inmutable tras caídas de corriente.
  - Resolución mDNS en `babylon.local:1234`.
  - Demonio permanente en `/Library/LaunchDaemons/com.babylon60.eridu-infer.plist`.

### 8.4. Protocolo Caballo de Troya (Shadow AI Pilot)
- Entrada mediante piloto sin coste de 7 días para auditar y frenar la fuga de datos confidenciales por uso de ChatGPT en empleados.
- Neutralización del veto del informático interno entregándole la ficha técnica de `SPEC.md` (cero puertos WAN, kernel en Rust, recibos criptográficos SCITT para el RGPD). Conversión histórica a compra >90%.

### 8.5. Ecuación de Salida M&A (3,5M € – 4,5M €)
- Con 35 a 50 unidades instaladas: ~500.000 € limpios acumulados en caja + 100.000 € a 120.000 € de ARR recurrente (churn = 0%).
- Teaser de venta para consultoras IT / integradores (Indra, Seidor, Telefónica Tech): adquisición por 3,5M € – 4,5M € (70% cash al cierre).
