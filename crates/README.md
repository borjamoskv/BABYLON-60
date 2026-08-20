# 📦 Crates — Componentes Rust Soberanos (Workspace Crates)

> **DOMINIO DE INGENIERÍA NATIVA**  
> Ubicación: `crates/`  
> Invariante: **INV-1 / Cero Anergía / C-ABI**

Este directorio aloja los sub-módulos nativos (`crates`) del núcleo Rust de BABYLON-60. A diferencia de `packages/` (orientado a integraciones Python/Node de alto nivel), la jerarquía de `crates/` constituye el corazón de la soberanía térmica, operando estrictamente en el Ring-0 agéntico.

## 📐 Catálogo de Crates Nativos

| Directorio | Propósito Funcional | Estatus Epistémico |
|---|---|---|
| `babylon60-kernel/` | Motor MOSKV-1 APEX, telemetría térmica, fail-stop (Art. 14(4)). | Core Sólido (C-ABI) |
| `babylon60-compiler/` | Compilador JIT/AOT de reglas deontológicas C5-REAL (Agente-Kant-Ω). | Phase Alpha |
| `babylon60-runtime/` | Máquina virtual determinista para operaciones lock-free (SPMC/SPSC). | Core Sólido |
| `babylon60-proof-ir/` | Intermediate Representation (IR) para integración con teoremas Lean 4. | Verificado |
| `babylon60-fuzz/` | Motores de *fuzzing* diferencial para validación de resistencia térmica. | QA Fuzzing |
| `cortex-guard/` | Sentinel Zero-Trust y oráculo de validación topológica en memoria. | Auditoría Activa |
| `nul-zk/` | Generador de DSLs en Arkworks para operaciones Cero Conocimiento. | Estable |
| `strike-rs/` | Gestor de operaciones deterministas y *dependency exhaustion*. | Experimental |

## 🛡️ Reglas Arquitectónicas (C5-REAL)
- **Zero-Copy Obligatorio:** Toda comunicación transversal entre crates debe usar *borrowing* estricto y buffers alineados a 64 bytes (evitando *false sharing*).
- **Prohibición de Arc/Mutex en ruta caliente:** La sincronización inter-crate debe delegarse a `seqlock` nativo (SPMC) en el `SharedManifest`.
- **Soberanía Binaria:** Todo crate debe ser capaz de compilar a `x86_64-unknown-linux-musl` u objetivo de Apple Silicon estático sin depender del OS.
