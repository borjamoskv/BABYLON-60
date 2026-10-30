# 📊 Estado del Proyecto y Resultados

<div align="center">

[Claims y niveles de evidencia](../CLAIMS.toml)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

Este documento orienta hacia las fuentes, ejemplos y comprobaciones del proyecto.
No registra una ejecución nueva de las pruebas. Los resultados dependen de la
revisión, las dependencias y el entorno identificados en cada informe.

---

## 1. 📌 Estado Actual (Lo que está construido)

Fuentes y pruebas disponibles para revisar el **Proof Harness**:

- **DSL y Kernel (Rust):** `src/babylon60.rs` implementa el intérprete del target `babylon60`. El tutorial comprueba un ejemplo compatible y delimita las proposiciones simuladas que añade ese intérprete.
- **Aritmética (`F60`):** Las representaciones, límites y operaciones dependen del intérprete o compilador seleccionado; una especificación de aritmética exacta no certifica todas sus rutas.
- **Monitor de Invariantes:** Los fixtures, entre ellos `tools/examples/falsation_test.b60`, describen casos que requieren ejecución y comprobación de su resultado. La presencia del archivo no demuestra por sí sola el rechazo.
- **Integración Formal (Lean 4):** `proof/lean/BabylonTrace.lean` define el modelo de trazas. Exportar un `proof.ir` desde el intérprete no ejecuta Lean ni acredita correspondencia con ese modelo.
- **Seguridad y DevOps:** Fuentes de pruebas en `tests/`, compilación Lean mediante `make test-lean` y auditorías configuradas en `.github/workflows/`. Cada resultado debe vincularse a la ejecución correspondiente.

## 2. 📌 Trabajo Futuro (Lo que es aspiracional)

- **Aislamiento de Singularidades Reales:** Actualmente, el motor *no* ha aislado un Finite-Time Blowup real de las ecuaciones de Navier-Stokes. Las pruebas actuales demuestran la viabilidad mecánica del arnés, pero no han resuelto el problema matemático.
- **Concurrencia en Entornos Distribuidos:** El *Event Ledger* funciona para sincronización en un único nodo, pero la validación topológica sobre clústeres distribuidos sigue en fase de diseño.

---

## 3. 🧮 Demostración Trivial (Prueba End-to-End)

El [tutorial causal](03_guides/tutorial_hello_causal.md) identifica el intérprete y
los ejemplos compatibles con esta revisión. Los programas de ejemplo se guardan
en `tools/examples/`; no en la raíz del checkout. Una ejecución del intérprete no
certifica automáticamente que su salida corresponde a un modelo Lean.

### Prerrequisitos
- Compilador de Rust (`cargo`)
- Entorno de Lean 4 configurado (`lake`)

### Ejecución

1. **Comprobar el inventario de ejecutables:**
   ```bash
   cargo metadata --locked --no-deps --format-version 1
   ```
   Este comando lista targets y manifiestos; no ejecuta ni verifica el kernel.

2. **Ejecutar pruebas del paquete raíz:**
   ```bash
   cargo test --locked -p babylon60_root --lib
   ```
   Conservar el comando, revisión, salida y recuento real. Un filtro vacío o una
   compilación sin pruebas no cuenta como validación del comportamiento.

3. **Compilar las fuentes formales:**
   ```bash
   make test-lean
   ```
   Este target ejecuta `lake build` en `proof/lean`. Compila los términos del
   modelo; no valida por sí solo cualquier ejecución del intérprete.

---
*Nota: Todo el ecosistema periférico (contratos inteligentes, dashboards web) ha sido desaprobado para centrar el esfuerzo de ingeniería exclusivamente en la robustez del Proof Harness.*

## Evidencia formal y límites

El bloque generado que concluía `True` se retiró: no demostraba ninguna propiedad
del intérprete ni de estos resultados. El modelo
[BabylonTrace.lean](../proof/lean/BabylonTrace.lean) contiene obligaciones sobre
trazas bajo sus hipótesis. El [informe de seguridad](security/kernel-audit-2026-10-15.md)
delimita las ejecuciones y pruebas que se observaron en su revisión.
