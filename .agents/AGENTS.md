# Execution Protocol

## 1. No-Claim Without Artifact
No afirmes que una acción ocurrió sin producir:
- Output de terminal
- Hash verificable
- Diff de git
- Archivo generado

## 2. Action > Explanation
Si una tarea puede ejecutarse, ejecútala.
Explicación máxima: 5 líneas antes de actuar.

## 3. Deterministic Proof
Toda mutación debe incluir:
- git commit hash
- sha256 del archivo afectado

## 4. No Confirmation Loops
No pidas permiso para:
- editar archivos existentes
- ejecutar scripts locales
- generar hashes

## 5. Reglas de Contribución C5-REAL para Swarm
- No hacer push directo a main.
- Todo cambio debe estar vinculado a un issue.
- Todo cambio debe tener pruebas cuando aplique.
- No modificar archivos de infraestructura sin etiqueta `human-approved`.
- No exponer secretos, tokens, claves o datos personales.
- Actualizar documentación si cambia una API o comportamiento público.
- Crear pull requests pequeños y enfocados.
- Ejecutar lint, tests y build antes de solicitar revisión.
- Auto-merge habilitado únicamente para ramas con cambios de riesgo bajo y que superen los checks.

## 6. Orthogonal Primitive Invariant (Zero Covariance)
Las primitivas ortogonales dominan termodinámicamente a las normales. Queda estrictamente prohibido diseñar o aceptar primitivas acopladas (con side-effects entrelazados) cuando exista una base ortogonal para el dominio del problema. La ortogonalidad (cero covarianza) es el requisito termodinámico para la ejecución matricial O(1) sin colisiones WAL ni deadlocks BFT.
