# ADR-004: Modelo de Aislamiento y Tracking de Taint

- **Estado:** Aceptada
- **Fecha:** 2026-08-10
- **Autor:** Borja Moskv (borjamoskv)

## Contexto

En un sistema multi-agente con FFI Rust-Python, se necesita un modelo de aislamiento que:
1. Prevenga la propagación de datos contaminados (tainted) entre componentes.
2. Garantice que un agente comprometido no pueda mutar el estado global sin pasar por el gate de verificación.
3. Cumpla con EU AI Act Art. 9 (gestión de riesgos) y Art. 10 (gobernanza de datos).

## Decisión

Se implementa un modelo de **taint tracking estático + fail-stop quarantine** con tres capas de aislamiento.

## Diseño

### Capa 1: Aislamiento de Proceso (FFI Boundary)

La frontera PyO3 actúa como un firewall de tipos:
- Los datos que cruzan de Python → Rust pasan por validación de tipos Pydantic (Python side) y deserialización tipada (Rust side).
- Los datos que cruzan de Rust → Python se serializan como tipos inmutables.
- No hay punteros compartidos entre runtimes.

### Capa 2: Taint Tracking (guards/)

El paquete `packages/babylon60/guards/` implementa decoradores de taint:
- `@tainted` marca datos que provienen de fuentes no verificadas (input de usuario, output de LLM).
- `@sanitized` marca datos que han pasado por verificación criptográfica.
- El motor de guards bloquea la propagación de datos `@tainted` a funciones que requieren `@sanitized`.

### Capa 3: Fail-Stop Quarantine

Si un componente detecta una violación de invariante:
1. El estado transiciona a `KernelState.Poisoned(code)` (formalizado en `BabylonTrace.lean`).
2. La transición es **irreversible** (demostrado formalmente: `poison_state_is_irreversible`).
3. Se genera un snapshot WORM (Write Once Read Many) del estado en el momento del fallo.
4. El pipeline de quarantine notifica vía el sistema de attestation.

## Consecuencias

- **Positivas:** Defense-in-depth con tres capas independientes. El fail-stop está verificado formalmente en Lean 4. Cumplimiento de EU AI Act Art. 9.
- **Negativas:** El taint tracking añade overhead cognitivo para desarrolladores. La quarantine irreversible puede causar false positives en producción.
- **Riesgo:** El taint tracking actual es a nivel de decoradores Python, no análisis estático completo (a diferencia de sistemas como TaintDroid o Jalangi). Mitigación: complementar con CodeQL taint analysis en CI.

## Referencias

- `tests/test_quarantine_snapshot.py` — Suite de validación de quarantine.
- `tests/test_inference_security.py` — Tests de seguridad de inferencia.
- `proof/lean/BabylonTrace.lean` — Prueba formal de irreversibilidad del estado Poisoned.
- EU AI Act, Artículos 9-10: Gestión de riesgos y gobernanza de datos.
