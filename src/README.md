# 🦀 SRC — Rust Sovereign Core & Sub-Kernels Nativos

> **NÚCLEO SOBERANO EN RUST (CRATE BASE & NATIVE KERNELS)**  
> El directorio `src/` contiene el código fuente en Rust compilable a través de `cargo build` / `cargo check`, junto con los subsistemas nativos del kernel en `src/kernel/`.

---

## 📐 Estructura de Módulos

```
src/
├── bin/
│   └── babylon60_kernel.rs       # Executable binario nativo de producción
├── kernel/                       # Módulos del Kernel Python/Rust (CDP Engine, Kimi, Quantum Sync, BFT)
│   └── README.md                 # Documentación detallada del subsistema kernel
├── agents/                       # Agentes nativos compilados
├── transducers/                  # Transductores polímatas nativos
├── babylon60.rs                  # BabylonVM & Parser de AST Cuneiforme Base-60
├── thermodynamics.rs             # Motores de física de la información y límites de Landauer
├── spsc.rs & spsc_ring.rs        # Ringbuffers SPSC lock-free para intercambio de ultra-baja latencia
├── seqlock.rs                    # Sincronización Seqlock de lectura sin bloqueos
├── proof_ir.rs                   # Representación Intermedia (IR) para circuitos de cero conocimiento
├── ffi.rs & ffi_python.rs        # Enlaces FFI de alta exergía (C-ABI & PyO3)
├── halt.rs                       # Disyuntor de emergencia (Emergency Circuit Breaker)
├── receipt.rs & manifest.rs      # Firmas Merkle, recibos de custodia y manifiesto del sistema
├── telemetry.rs & c5_telemetry.py# Telemetría en tiempo real
└── generated_aphairesis_constants.rs # Constantes axiomáticas calibradas
```

---

## 🔍 Taxonomía de los Módulos Rust

### 1. `babylon60.rs` — BabylonVM & Cuneiform Parser
* Implementa la Máquina Virtual `BabylonVM` que ejecuta instrucciones `MUB`, `GIN`, `TUKU`, `NU`, `WAL`, `ADD`, `DEC` y `OUT`.
* Filtra alucinaciones evaluando constantes numéricas en caracteres cuneiformes sexagesimales (`<`=10, `Y`=1).

### 2. `thermodynamics.rs` — Motor Termodinámico & Exergía
* Calcula la exergía de la información y aplica la cota de Landauer ($\Delta S \ge k_B \ln 2$) en las transformaciones del sistema.

### 3. `spsc.rs` / `spsc_ring.rs` / `seqlock.rs` — Estructuras Concurrente Lock-Free
* Permite la transferencia de datos entre el hilo principal y los trabajadores BFT sin cerrojos de mutex, minimizando la latencia IPC.

### 4. `proof_ir.rs` — Representación Intermedia de Pruebas ZK
* Representación en grafo de restricciones R1CS para integración con probadores criptográficos.

### 5. `halt.rs` — Emergency Circuit Breaker
* Salvaguarda determinista que aborta la ejecución si se detectan violaciones de estabilidad estructural o manipulaciones de memoria.

---

## 🛠️ Comandos de Compilación & Verificación

```bash
# Verificación de compilación nativa en Rust
cargo check

# Compilación optimizada de release
cargo build --release

# Ejecución de tests de integración en Rust
cargo test
```
