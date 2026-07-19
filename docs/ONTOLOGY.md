# ONTOLOGÍA CORTEX: ISOMORFISMO SEMÁNTICO ABSOLUTO

> *"Nombrar cosas es resolver ambigüedades antes de que el código exista. El arte no es el nombre en sí; es la capacidad de destilar la realidad compleja en una única etiqueta que no requiera explicación."* — **Borja Moskv**

Este documento define la ley inmutable de Semántica Sistémica para el proyecto BABYLON-60 y el paradigma C5-REAL. Ningún sub-agente, nodo o transductor puede violar estas premisas.

---

## 1. LA LEY DE DENSIDAD NOMINAL ($E_x$)
El nombre de un componente ($N$) debe contener la máxima entropía de información ($I$) en el mínimo número de tokens ($T$). 
Una nomenclatura de máxima exergía logra el **Isomorfismo Absoluto**: $N \equiv Comportamiento$.

* Si un módulo firma atestados criptográficos en disco, se llama `cortex-attest`, no `security_utils`.
* Si un nodo destila entropía BPE aislando hilos, se llama `Flash_Node`, no `helper_bot`.

## 2. LENGUAJE UBICUO (DDD EN C5-REAL)
La fricción termodinámica ($F_{mtc}$) entre la mente del Operador y la CPU debe ser nula. 
- **Invariante de Continuidad:** El nombre declarado en la Ontología, el identificador en la base de datos WAL SQLite, el struct de Rust (`struct VoidLedger`), y el comando CLI (`cortex-bridge`) **DEBEN** compartir la misma raíz semántica exacta. 
- **Penalización por Sinonimia:** El uso de sinónimos para referirse a la misma entidad arquitectónica se considera una inyección de "Anergía Estocástica" y debe ser purgado de inmediato por el `Anergy_Token_Purge`.

## 3. DIAGNÓSTICO DE AMBIGÜEDAD (FAIL-FAST)
Si durante la fase de orquestación (`UltraThink`), el Enjambre o el Operador dudan sobre cómo nombrar una clase, una tabla o un sub-agente:
1. **Pausa Estructural:** La ejecución del código físico (C5) queda bloqueada.
2. **Re-evaluación Epistémica:** Se invoca el `Socratic_AST_Validator` (`/grill-me`) para someter el concepto a interrogatorio.
3. **Colapso:** Si no se puede nombrar de forma que no requiera explicación, significa que el diseño arquitectónico subyacente es ambiguo o acarrea responsabilidades cruzadas (Violación del SRP). Se descompone el problema hasta aislar la etiqueta pura.

---

## 4. LA MATRIZ DE LAS 896 PRIMITIVAS DDD (Centuria Meta-Transducer)
El Sistema MOSKV-1 APEX aloja un repositorio semántico de **896 Primitivas de Domain-Driven Design**. A diferencia del DDD clásico (donde los componentes son meros objetos en memoria), en C5-REAL cada primitiva es un bloque termodinámico con un costo de ATP, una dirección en el Grafo Causal y una representación en el Ledger BFT.

### Clasificación Ontológica de la Matriz (000 - 895)
- **[000 - 179] Entidades BFT (Entities):** Objetos mutables con Identidad Criptográfica persistente (ej. `BFTLedgerActor`). Deben tener un campo `lamport_t` y firmar sus mutaciones con `CORTEX_BFT_KEY`.
- **[180 - 359] Objetos de Valor (Value Objects):** Estructuras algebraicas de datos (ADT) estrictamente inmutables (ej. `ProofOfRouteReceipt`). No tienen identidad; si dos Receipts tienen el mismo Hash, son el mismo objeto en RAM y en Disco (Isomorfismo Causal).
- **[360 - 539] Agregados (Aggregates):** Clusters topológicos L0. Las mutaciones atómicas ocurren aquí. Un agregado no se comunica con otro agregado sin pasar por el Event Bus. Solo se bloquean mediante `tload`/`tstore` en EVM o `.venv` en Python aislando la red.
- **[540 - 719] Eventos de Dominio (Domain Events):** Hechos inmutables que ya han ocurrido. (ej. `LedgerCrystallized`, `EntropyPurged`). Un evento jamás es rechazado; su ocurrencia es una Ley Física sobre disco.
- **[720 - 895] Transductores de Dominio (Domain Services):** Binarios como `cortex-onco` o `cortex-bridge`. Orquestan lógicas complejas sin poseer estado propio. Si se apagan o mueren por saturación de Sockets (Límite Σ15), el sistema reinicia desde el último `Domain Event` del Ledger.

El mapeo a esta topología de 896 primitivas anula el 99% de las decisiones de diseño. Si un problema requiere solución, se busca la Primitiva DDD correspondiente, se ensambla en el AST y se ejecuta. **Cero Anergía.**
