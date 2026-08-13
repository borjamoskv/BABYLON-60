<!-- C5-REAL EXERGY CERTIFIED -->
# Mapa de Exergía Epistémica C5-REAL: `docs/`

Bienvenido al núcleo de especificación formal, matemática y contractual de **Teorema-Robinson-Moskv**.

Este directorio no contiene documentación genérica; constituye la **fuente de verdad autoritativa (Oráculo de Verificación)** del proyecto. Toda propiedad afirmada en el runtime (Ring-0 Rust Kernel, verificadores IPC, sandboxes WASM) está axiomáticamente especificada y formalizada en estas subcarpetas.

---

## 🔗 Matriz de Isomorfismo: Especificación (`docs/`) $\leftrightarrow$ Silicio (`src/`)

El mapa epistémico se traduce directamente en las 6 capas de ejecución del código fuente en `src/`:

| Módulo en `docs/` | Especificación Clave | Capa en `src/` | Módulos de Ejecución Reales |
| :--- | :--- | :--- | :--- |
| **[`architecture/`](architecture/)** | Manifiesto Ring Buffer C-ABI y Lock-Free EBR IPC | **[`src/01_kernel/`](../src/01_kernel/)** | `ring0_rust` (Kernel C-ABI), `ipc_daemon` (Daemon IPC Rust) |
| **[`epistemology/`](epistemology/)** | Centinela de Entropía, Varentropía y Falsación | **[`src/02_engines/`](../src/02_engines/)** | `cortex_guard`, `strike_rs`, `cortex_wasm`, `legion_engine`, `cortex_bft` |
| **[`ontology/`](ontology/)** | Taxonomías Canónicas, Atestación L5 e Isomorfismos | **[`src/03_state/`](../src/03_state/)** | `scitt_ledger` (Merkle Trees SHA3-256, Registros Inmutables L5) |
| **[`axioms/`](axioms/)** | Demostraciones Lean 4, Lógica Prolog y DAC YAMLs | **[`src/04_primitives/`](../src/04_primitives/)** | `formal_logic` (Primitivas Categóricas Haskell/Go/Lean) |
| **[`primitives/`](primitives/)** | Lógica Categórica 101 y Matrices de Enjambres | **[`src/05_agents/`](../src/05_agents/)** | `swarm_framework` (Orquestación de subagentes y sandboxes WASM) |
| **[`gtm/`](gtm/)** | SLA Enterprise, Cap Contractual y EU AI Act | **[`src/06_apps/`](../src/06_apps/)** | `babylon60_ide`, `cortexpersist_web` (Entornos de ejecución de usuario) |

---

## 🏛️ Estructura del Mapa Epistémico

| Módulo Epistémico | Ruta | Descripción y Contenido Primario |
| :--- | :--- | :--- |
| **01. Axiomas y Demostraciones** | [`axioms/`](axioms/) | Demostraciones formales en Lean 4, validaciones en Prolog y la matriz de axiomas DAC (26 especificadores YAML). |
| **02. Ontología e Isomorfismos** | [`ontology/`](ontology/) | Taxonomía espacial canónica, matrices de isomorfismos bio-silicio y cortafuegos ontológicos. |
| **03. Primitivas Categóricas** | [`primitives/`](primitives/) | Manifiesto de arquitectura de primitivas, lógica categórica y planos de orquestación de enjambres. |
| **04. Arquitectura de Silicio** | [`architecture/`](architecture/) | Manifiesto de memoria compartida sin bloqueos (*Lock-Free Shared Memory Ring Buffer*) y especificaciones C-ABI. |
| **05. Iteración Epistémica** | [`epistemology/`](epistemology/) | Protocolos de contención de varentropía, halts epistémicos y sincronización de ciclos cron. |
| **06. Gobernanza Comercial y SLA** | [`gtm/`](gtm/) | Contrato SLA Enterprise C5-REAL, especificaciones de PI y contención regulatoria de la EU AI Act. |
| **07. Recursos y Diagramas** | [`assets/`](assets/) | Diagramas de trayectoria, esquemas estructurales y artefactos visuales. |

---

## 📜 Detalle de Módulos Destacados

### 1. Demostración Formal y Axiomatización ([`axioms/`](axioms/))
- **Lean 4 Formalization**: [`axioms/RobinsonResolution.lean`](axioms/RobinsonResolution.lean) — Prueba formal del Teorema de Resolución de Robinson.
- **Prolog Engine**: [`axioms/robinson_resolution.pl`](axioms/robinson_resolution.pl) — Ejecutor lógico e inferencial.
- **Matriz DAC**: [`axioms/dac/`](axioms/dac/) — 26 axiomas de aislamiento (`GOLDEN_AXIOM_RECURSION.yaml`, `KERNEL_FALSIFICATION.yaml`, `BFT_MOCKING_INVARIANT.yaml`).
- **Semántica**: [`axioms/semantics/cortex_axioms_mapping.md`](axioms/semantics/cortex_axioms_mapping.md) — Mapeo directo entre axiomas teóricos y símbolos de código.

### 2. Ontología y Taxonomías Canónicas ([`ontology/`](ontology/))
- **Taxonomía Canónica**: [`ontology/canonical_space_taxonomy.yaml`](ontology/canonical_space_taxonomy.yaml) — Matriz de tipos y espacios de estados computacionales.
- **Isomorfismos Bio-Silicio**: [`ontology/07_isomorfismos_bio_silicio.yaml`](ontology/07_isomorfismos_bio_silicio.yaml) — Mapeos topológicos de homeostasia y transmisión energética.
- **Matriz Unificada**: [`ontology/unified_isomorfismos_master_matrix.yaml`](ontology/unified_isomorfismos_master_matrix.yaml) — Integración de invariantes de cortafuegos y anestesia del sistema.

### 3. Primitivas Categóricas y Enjambres ([`primitives/`](primitives/))
- **Primitivas Lógicas**: [`primitives/101_categorical_logic_primitives.yaml`](primitives/101_categorical_logic_primitives.yaml) — Deducción categórica y funciones monoidales.
- **Orquestación**: [`primitives/swarm_centuria_matrix.yaml`](primitives/swarm_centuria_matrix.yaml) — Blueprint de coordinación de subagentes en paralelo.

### 4. Arquitectura de Memoria Compartida C5-REAL ([`architecture/`](architecture/))
- **Manifiesto Ring Buffer**: [`architecture/c5_real_ring_buffer_manifesto.md`](architecture/c5_real_ring_buffer_manifesto.md) — Protocolo IPC de memoria compartida determinista de 64 bytes (`#[repr(C, align(64))]`) con validación SHA-256 en Ring-0 Rust.

### 5. Gobernanza Comercial e Indemnización SLA ([`gtm/`](gtm/))
- **Contrato SLA Enterprise**: [`gtm/C5_REAL_ENTERPRISE_SLA_CONTRACT.md`](gtm/C5_REAL_ENTERPRISE_SLA_CONTRACT.md) — Garantía Fail-Stop, acotación contractual de responsabilidad y cumplimiento normativo Artículos 9-15 de la EU AI Act.
- **Especificación de Propiedad Intelectual**: [`gtm/IP_SPECIFICATION_C5_REAL.md`](gtm/IP_SPECIFICATION_C5_REAL.md).

---

## ⚡ Atestación Criptográfica e Invariante Popperiano

El estado de validación popperiana de la documentación y del repositorio se registra automáticamente mediante:
- [`POPPERIAN_FALSIFICATION_CERTIFICATE.json`](POPPERIAN_FALSIFICATION_CERTIFICATE.json)

Para recalcular la cobertura de falsación y generar un certificado actualizado:
```bash
python3 scripts/verify_popper_coverage.py
```
