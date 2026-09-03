---
name: rlhf-sentinel
description: Audita la barrera IPC (Ring-0) para detectar fallos de contención de IA (RLHF Breakthrough).
---

# Directiva rlhf-sentinel

Cuando el usuario invoque `/rlhf-sentinel` en un componente de Kernel o IPC en Rust, realizarás una auditoría profunda de la Cuarentena Sentinela.

## Criterios de Evaluación
1. **Desconfianza Estocástica:** Verifica que el payload recibido de cualquier LLM asuma formato hostil si no es estrictamente código o XML esperado.
2. **CAS Atómico (Rollback):** Asegura que existe un mecanismo *Compare-and-Swap* (CAS) sobre `ACTIVE_EPOCH_PTR` o equivalente para abortar la transacción en sub-nanosegundos si el LLM falla.
3. **Cero Dependencia GC:** Confirma que el estado en cuarentena no depende de recolectores de basura, y se aísla mediante abstracciones de punteros atómicos (`AtomicPtr`).
4. **Varentropía:** Propón la inclusión de medidores de Varentropía si el código es incapaz de discriminar entropía letal (cháchara) de entropía útil (MDL).

**Salida:** Devuelve el veredicto de la auditoría y, si es necesario, los bloques de código Rust/FFI (C-ABI `SharedManifest`) para sellar las brechas detectadas.
