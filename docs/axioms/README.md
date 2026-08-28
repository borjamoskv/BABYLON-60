<!-- C5-REAL EXERGY CERTIFIED -->
# Módulo Epistémico: Axiomas y Demostraciones Formales (`docs/axioms/`)

Este subdirectorio contiene las demostraciones lógicas, formalizaciones en Asistentes de Pruebas (Lean 4), validadores lógicos en Prolog y la matriz completa de especificaciones de axiomas DAC (*Deterministic Axiom Controls*).

---

## 🔗 Vinculación con Silicio (`src/`)

- **Capa en `src/`**: [`src/04_primitives/formal_logic/`](../../src/04_primitives/formal_logic/)
- **Propósito**: Proveer los predicados formales y teoremas que el compilador y los verificadores estáticos en Go/Haskell/Rust utilizan para validar la ausencia de alucinación y la decidibilidad de transiciones.

---

## 📂 Inventario de Artefactos

### 1. Demostraciones Formales e Inferenciales
- [`RobinsonResolution.lean`](RobinsonResolution.lean): Demostración formal en **Lean 4** del Teorema de Resolución de Robinson para lógica de primer orden.
- [`robinson_resolution.pl`](robinson_resolution.pl): Motor inferencial y regla de resolución de Robinson implementada en **Prolog**.
- [`robinson_test.pl`](robinson_test.pl): Suite de pruebas unitarias lógicas en Prolog.

### 2. Matriz DAC (*Deterministic Axiom Controls*) — [`dac/`](dac/)
Colección de 26 especificadores YAML que imponen restricciones invariantes en el Kernel:
- [`dac/10_KERNEL_AXIOMATIZATION.yaml`](dac/10_KERNEL_AXIOMATIZATION.yaml): Axiomatización primordial del Kernel C5.
- [`dac/KERNEL_FALSIFICATION.yaml`](dac/KERNEL_FALSIFICATION.yaml): Criterios popperianos de falsabilidad empírica.
- [`dac/GOLDEN_AXIOM_RECURSION.yaml`](dac/GOLDEN_AXIOM_RECURSION.yaml): Invariante de convergencia recursiva.
- [`dac/GOLDEN_AXIOM_BIO_SILICIO.yaml`](dac/GOLDEN_AXIOM_BIO_SILICIO.yaml): Isomorfismo topológico bio-silicio.
- [`dac/HYPERVISOR_AXIOMS.yaml`](dac/HYPERVISOR_AXIOMS.yaml): Reglas de contención en sandbox de Ring-0.
- [`dac/BFT_MOCKING_INVARIANT.yaml`](dac/BFT_MOCKING_INVARIANT.yaml): Tolerancia a fallos bizantinos.
- [`dac/ULTRATHINK_9NODE.yaml`](dac/ULTRATHINK_9NODE.yaml) & [`dac/ULTRATHINK_BFT_ORCHESTRATION.yaml`](dac/ULTRATHINK_BFT_ORCHESTRATION.yaml): Protocolo Ultrathink de 9 nodos.
- [`dac/SLOP_HORIZON.yaml`](dac/SLOP_HORIZON.yaml) & [`dac/LINNAEAN_SYCOPHANCY.yaml`](dac/LINNAEAN_SYCOPHANCY.yaml): Erradicación de complacencia y ruido variacional.

### 3. Semántica y Mapeo ([`semantics/`](semantics/))
- [`semantics/cortex_axioms_mapping.md`](semantics/cortex_axioms_mapping.md): Mapeo bi-unívoco entre identificadores de axiomas y símbolos de funciones en el código fuente.
- [`semantics/nomenclator.md`](semantics/nomenclator.md): Glosario semántico formal de símbolos y operadores.
