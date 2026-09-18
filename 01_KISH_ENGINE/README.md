# 📦 PACKAGES — Monorepo Core & Subsistemas Canónicos BABYLON-60

> **NÚCLEO DE PRODUCCIÓN Y SUBSISTEMAS DISTRIBUIDOS**  
> El directorio `packages/` contiene el código fuente canónico, módulos de consenso BFT, transductores termodinámicos, guardias de capacidad, atestación criptográfica y servicios de infraestructura de **BABYLON-60**.

---

## 🏛️ Taxonomía de Paquetes Principales

```
packages/
├── babylon60/              # Paquete principal Python/Rust de BABYLON-60
│   ├── bft/                # Consenso BFT, actores de ledger y colas de estado
│   ├── guards/             # Salvaguardas, validadores soberanos y contratos Saga
│   ├── transducers/        # Transductores termodinámicos, compresión Landauer y pulso semántico
│   ├── primitives/         # Primitivas C5-REAL (Base-60, CBOR, Matrices de desintegración)
│   ├── attestation/        # Anclaje Merkle y atestación de integridad
│   ├── verification/       # Gradación AST, falsación Popperiana y verificación de contraejemplos
│   ├── compliance_exporter/# Exportación de cumplimiento (EU AI Act, i18n)
│   ├── compiler/           # Backend de compilación formal a Lean 4
│   ├── commands/           # Comandos CLI interactivos (itera, grill_you, strict_reviewer)
│   └── verifiable_inference/ # Motor nativo de inferencia verificable en Rust (Cargo)
├── cortex/                 # Motor de almacenamiento de hechos, contexto e inferencia CORTEX
├── extensions/             # Extensiones modulares del sistema (Raft, Swarm, Sync)
├── logs/                   # Subsistema de custodia de logs de alta exergía
└── services/               # Servicios de infraestructura serverless (Cloudflare Worker email_inbound)
```

---

## 🔍 Resumen por Módulo Canónico

### 1. `packages/babylon60/bft/` — Consenso & Ledger Activo
* **`consensus_ledger.py` & `cortex_persist_ledger.py`**: Libro mayor BFT persistente con tolerancia a fallos bizantinos.
* **`consensus_validator.py` & `consensus_committer.py`**: Validación y commit determinista de bloques.
* **`exergy_binary_ipc.py`**: Comunicación IPC de alta exergía entre procesos de Rust y Python.
* **`bayesian_swarm.py`**: Enjambre bayesiano de consenso distribuido.

### 2. `packages/babylon60/guards/` — Salvaguardas & Seguridad Zero-Trust
* **`capability_guard.py` & `capabilities.py`**: Aislamiento estricto por capacidades (Zero-Trust).
* **`contradiction_guard.py`**: Detector de contradicciones lógicas y entropía C4-SIMULACIÓN.
* **`license_sovereign_validator.py` & `license_verifier.py`**: Validación criptográfica de licencias soberanas.
* **`saga_contract.py`**: Transacciones distribuidas compensatorias (Patrón Saga).

### 3. `packages/babylon60/transducers/` — Termodinámica & Compresión
* **`landauer.py`**: Medición del límite entrópico de Landauer ($k_B T \ln 2$) en transformaciones de datos.
* **`compression.py` & `turboquant.py`**: Compresión de alta exergía y cuantización de información.
* **`semantic_heartbeat.py` & `pulmones.py`**: Latido semántico y trabajador de ventilación del sistema.
* **`hygiene.py`**: Limpieza e higiene continua del estado en memoria.

### 4. `packages/babylon60/primitives/` — Primitivas C5-REAL
* **`base60.py`**: Codificación Sexagesimal Babilónica (Base-60).
* **`disintegration_matrix.py` & `matrix.py`**: Matrices de desintegración bayesiana y transformaciones lineales.
* **`serialization_boundary.py` & `cbor.py`**: Serialización binaria determinista.
* **`tonnetz_monitor.py`**: Monitor de armónicos Tonnetz para análisis psychoacústico/sistémico.

### 5. `packages/babylon60/verification/` — Verificación Formal
* **`verifier.py` & `ast_grader.py`**: Evaluador de árboles sintácticos y oráculo de falsabilidad Popperiana.
* **`counterexample.py`**: Generador de contraejemplos para falsación de proposiciones.

### 6. `packages/babylon60/verifiable_inference/` — Inferencia Verificable (Rust)
* Proyecto nativo Cargo/Rust que compila el motor de inferencia criptográficamente verificable con firmas de ejecución.

### 7. `packages/services/email_inbound/` — Pasarela Serverless
* Worker de Cloudflare (`worker.js` / `wrangler.toml`) para captura e ingestión de emails entrantes directo a la cola CORTEX.
