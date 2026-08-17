# HANDOFF.md — Protocolo Soberano de Traspaso de Contexto C5-REAL

---

## 🎯 Objetivo Global
Formalizar, verificar e inmunizar el substrato híbrido Rust/Python/Solidity/SMT de **BABYLON-60 / Teorema-Robinson-Moskv**, auditando su gobernanza de IA (EU AI Act, Lean 4, SAST/DAST) y garantizando la contención de anergía termodinámica y el linaje de datos criptográfico.

---

## ✅ Delta Exergético (Avances Verificados Empíricamente)

| Componente | Archivo / Artefacto | Descripción del Cambio / Verificación |
| :--- | :--- | :--- |
| **Kernel Ledger Rust** | [`crates/babylon60-kernel/src/ledger.rs`](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/crates/babylon60-kernel/src/ledger.rs) | Implementada la estructura del libro mayor determinista con validación de hashes Chentsov y barrera AOF. |
| **Axiom Verifier Z3** | [`scripts/c5_verifiers/axiom_verifier_z3.py`](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/scripts/c5_verifiers/axiom_verifier_z3.py) | Añadido verificador formal de axiomas en Z3 con control estricto de timeout e inmunización contra vacuidad lógica. |
| **FFI Python Interface** | [`src/ffi_python.rs`](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/src/ffi_python.rs) & [`test_pyo3.py`](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/test_pyo3.py) | Exposición segura de primitivas Rust a Python vía PyO3 con aislamiento de memoria in-process y manejo de excepciones C5. |
| **Apoptosis Smart Contract** | [`experiments/anvil_yung/script/DeployApoptosisAnchor.s.sol`](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/experiments/anvil_yung/script/DeployApoptosisAnchor.s.sol) & [`scripts/c5_simulations/testnet_apoptosis_notary.py`](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/scripts/c5_simulations/testnet_apoptosis_notary.py) | Anclaje y notaría de auto-destrucción y purga entrópica para agentes en testnet EVM / Anvil. |
| **Audit & Valuation Engine** | [`packages/babylon60/verification/z3_compiler.py`](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/packages/babylon60/verification/z3_compiler.py) | Compilación formal de constraints Z3 y barreras de atestación para auditoría de gobernanza (EU AI Act + Lean 4). |

---

## 📍 Punto Fijo $\Omega$ (Estado de Detención e Invariantes)

- **Binarios / Cargas Cargo:** Todos los tests de Rust ejecutan con éxito (`cargo test` -> PASS en 30+ tests del kernel).
- **Suite Pytest (`pytest`):** 65 PASSED, 2 SKIPPED, 1 XFAILED, 1 FAILED.
  - **Fallo Identificado:** `tests/test_c5_invariants.py::test_inv_c5_13_nesting_depth_ceiling`
  - **Causa Raíz:** Violación del techo de profundidad de anidamiento AST (`nesting depth <= 4`) en [`packages/babylon60/verification/z3_compiler.py`](file:///Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/packages/babylon60/verification/z3_compiler.py):
    - L197: `_extract_field()` tiene anidamiento profundidad 6 (> 4).
    - L413: `emit_sort()` tiene anidamiento profundidad 6 (> 4).
- **Git HEAD Branch:** `965906f1cc feat(verifiers): añadir verificador de exergía ontológica de datos (C5-REAL)`
- **Working Tree:** 4 archivos modificados y 10 artefactos de simulación/auditoría no rastreados.

---

## 🧠 Matriz de Gotchas y Reglas Invariables

> [!IMPORTANT]
> **Aislador Z3 SMT:** Al invocar solvers Z3 en Python o Rust, SIEMPRE fijar `rlimit` / `timeout` explícito. Las consultas unificadas sobre grafos de estados profundos pueden provocar explosión combinatoria.

> [!WARNING]
> **Maturin / PyO3 Feature Flag:** En `Cargo.toml`, asegurar que `features = ["pyo3/extension-module"]` esté correctamente asignado cuando se construye como módulo Python, pero excluido al compilar como binario soberano standalone (`c5-sovereign-binary`).

> [!NOTE]
> **Lectura Epistémica de Logs:** Respetar la regla `user_global` de interpretación no destructiva de auditorías o transcripciones pegadas. Son de solo lectura a menos que exista comando imperativo de purga.

---

## 🚀 Grafo de Acción $O(1)$ (Secuencia de Entrada para la Siguiente Sesión)

Para reanudar el estado sin reconstrucción entrópica de contexto, ejecutar la siguiente secuencia de comandos determinista:

1. **Verificar Tests del Kernel Rust:**
   ```bash
   cargo test --quiet
   ```

2. **Compilar e Instalar Módulo Python (Maturin):**
   ```bash
   maturin develop --release
   ```

3. **Ejecutar Suite Completa de Tests Python:**
   ```bash
   pytest -v
   ```

4. **Ejecutar Verificación Formal Z3 de Axiomas C5-REAL:**
   ```bash
   python3 scripts/c5_verifiers/axiom_verifier_z3.py
   ```
