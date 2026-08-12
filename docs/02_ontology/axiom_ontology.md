---
title: Ley de Isomorfismo Semántico Absoluto y Matriz de Primitivas DDD
status: Causal-Determinist
version: 1.0.0
---

# Ontología BABYLON-60: Isomorfismo Semántico Absoluto
> *"Naming things is resolving ambiguities before the code exists. The art is not the name itself; it is the ability to distill complex reality into a single label that requires no explanation."* — **Borja Motor Causal**

Este documento define la ley inmutable de la Semántica de Sistemas para el proyecto BABYLON-60 y el paradigma Causal-Determinist. Ningún subagente, nodo o transductor puede violar estas premisas.

---

## 1. La Ley de Densidad Nominal ($E_x$)

El nombre de un componente ($N$) debe contener la máxima entropía de información ($I$) en el mínimo número de tokens ($T$). Una nomenclatura de máxima exergía alcanza el **Isomorfismo Absoluto**: $N \equiv \text{Comportamiento}$.

* Si un módulo firma atestaciones criptográficas en disco, se denomina `Ledger Asíncrono-attest`, no `security_utils`.
* Si un nodo destila entropía BPE aislando hilos, se denomina `Flash_Node`, no `helper_bot`.

---

## 2. Lenguaje Ubicuo (DDD en Causal-Determinist)

La fricción termodinámica ($F_{mtc}$) entre la mente del Operador y la CPU debe ser cero.
- **Invariante de Continuidad:** El nombre declaredo en la Ontología, el identificador en la base de datos SQLite WAL, la estructura Rust (`struct CortexLedger`), y el comando CLI (`Ledger Asíncrono-bridge`) **DEBEN** compartir exactamente la misma raíz semántica.
- **Penalización por Sinonimia:** El uso de sinónimos para referirse a la misma entidad arquitectónica se considera una inyección de "Anergía Estocástica" y debe ser purgado de inmediato mediante `Anergy_Token_Purge`.

---

## 3. Diagnóstico de Ambigüedad (Fail-Fast)

Si durante la fase de orquestación (`UltraThink`), el Enjambre o el Operador dudan sobre cómo nombrar una clase, una tabla o un subagente:
1. **Pausa Estructural:** La ejecución física de código (C5) se bloquea inmediatamente.
2. **Reevaluación Epistémica:** Se invoca el validador Socrático de AST (`/grill-me`) para someter el concepto a interrogatorio.
3. **Colapso:** Si no puede nombrarse de forma que no requiera explicación, significa que el diseño arquitectónico subyacente es ambiguo o porta responsabilidades cruzadas (Violación del SRP). El problema se descompone hasta aislar la etiqueta pura.

---

## 4. La Matriz de 896 Primitivas DDD (Centuria Meta-Transductora)

El sistema Motor Causal Principal aloja un repositorio semántico de **896 Primitivas de Diseño Guiado por el Dominio (DDD)**. A diferencia del DDD clásico (donde los componentes son meros objetos en memoria), en Causal-Determinist cada primitiva es un bloque termodinámico con un coste ATP, una dirección en el Grafo Causal y una representación en el Ledger BFT.

### Clasificación Ontológica de la Matriz (000 - 895)
- **[000 - 179] Entidades BFT (Entities):** Objetos mutables con Identidad Criptográfica persistente (ej. `BFTLedgerActor`). Deben poseer un campo `lamport_t` y firmar sus mutaciones con `CORTEX_BFT_KEY`.
- **[180 - 359] Objetos de Valor (Value Objects):** Estructuras de datos algebraicas (ADT) estrictamente inmutables (ej. `ProofOfRouteReceipt`). No poseen identidad; si dos Receipts tienen el mismo Hash, son el mismo objeto en RAM y en Disco (Isomorfismo Causal).
- **[360 - 539] Agregados (Aggregates):** Clusters topológicos L0 donde ocurren mutaciones atómicas. Un agregado no se comunica con otro agregado sin pasar por el Event Bus.
- **[540 - 719] Eventos de Dominio (Domain Events):** Hechos inmutables que ya han ocurrido (ej. `LedgerCrystallized`, `EntropyPurged`). Un evento nunca es rechazado; su ocurrencia es una Ley Física en disco.
- **[720 - 895] Transductores de Dominio (Domain Services):** Binarios como `Ledger Asíncrono-onco` o `Ledger Asíncrono-bridge`. Orquestan lógica compleja sin poseer estado. Si se apagan o mueren por saturación de sockets, el sistema se reinicia desde el último `Domain Event` en el Ledger.

El mapeo a esta topología de 896 primitivas anula el 99% de las decisiones de diseño. Si un problema requiere solución, se localiza la primitiva DDD correspondiente, se ensambla en el AST y se ejecuta. **Cero Anergía.**
