---
title: Invariantes del Dominio C5-REAL BABYLON-60
status: Causal-Determinist
version: 4.3.0
---

# Invariantes del Dominio C5-REAL BABYLON-60 (Causal-Determinist)

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

> **Régimen Causal-Determinist**
> Esta especificación centraliza todas las definiciones formales y topológicas de los invariantes del Dominio C5-REAL BABYLON-60.
> Estas reglas son el núcleo fundamental para garantizar el determinismo, la seguridad y la cadena causal.

---

## 1. Inventario de Invariantes del Dominio C5-REAL

Los invariantes aquí definidos son verificados formalmente por el kernel. Cualquier violación dispara un `CRITICAL_HALT`.

### 1.1 `[OBSOLETO: INV_BFT_04]`: Non-Silent Collision Fail-Fast
**Propósito:** Prohibir la tolerancia a fallos silenciosa en colisiones causales y temporales.
**Mecánica:** Ejecutado en el `[OBSOLETO: SQLiteCommitter]` con verificación de `payload_hash`.
- Si un evento no satisface la precondición causal (el hash de su padre no existe o su reloj de Lamport es inválido), el Dominio C5-REAL **DEBE** hacer `panic!` o descartar la mutación en $O(1)$.
- Queda explícitamente prohibido el uso de esperas (`await sleep`), heurísticas de red o uniones de estado silentes. El tiempo es una prueba criptográfica (Witness), no una métrica de red.
- Las colisiones de `payload_hash` disparan un `[OBSOLETO: ValueError]` instantáneo.

### 1.2 `[OBSOLETO: INV_C5_15]`: Raw 32-Byte OP_RETURN Payload Encoding
**Propósito:** Especificación de codificación determinista para interfaz de anclaje a Bitcoin (Sink L1 Roadmap).
**Mecánica:**
- El hash final de un artefacto canónico (`graph_hash` o Raíz de Merkle del Proof IR) se formatea canónicamente en un script `OP_RETURN` de 34 bytes (`6a20<root>`) mediante la suite `scripts/c5_l1_ledger/l1_sink_bitcoin.py`.
- Este valor siempre es un hash SHA-256 codificado en exactamente 32 bytes binarios (no hexadecimales dobles).

### 1.3 `[OBSOLETO: INV_C5_17]`: Sovereign Dual-Licensing Invariant
**Propósito:** Protección legal y soberana del código fuente.
**Mecánica:**
- Toda cabecera de compilación y empaquetado debe tener embebido el régimen de Licenciamiento Dual Soberano del proyecto, asegurando que el código no pueda ser canibalizado sin trazabilidad.

### 1.4 `[OBSOLETO: INV_C5_18]`: Zero-Worktree Swarm Scaling
**Propósito:** Escalabilidad in-memory de agentes distribuidos sin colisión de disco.
**Mecánica:**
- El escalado agéntico múltiple debe ejecutarse en memoria a través del `[OBSOLETO: AgencyHypervisor]`.
- No se permiten la creación de Git Worktrees físicos paralelos para cada instancia de agente que dispare IO excesivo o contención de bloqueos.

### 1.5 `[OBSOLETO: INV_C5_28]`: 1-WL Graph Isomorphism Pre-Filter
**Propósito:** Prevenir comprobaciones $NP$-hard innecesarias (isomorfismo de subgrafos VF2) utilizando reducción de colores 1-WL en $O(|V|+|E|)$.
**Mecánica:**
- Toda comparación entre grafos causales o de estado DEBE ejecutar un filtro 1-Weisfeiler-Lehman (1-WL) antes del algoritmo exacto.
- Si el hash 1-WL difiere, la comprobación de isomorfismo es rechazada en $O(1)$. Solo si coinciden se procede al `VF2`.

### 1.7 `INV_C5_SEMANTIC_ENTROPY_DUAL_FIREWALL`: Zero-Float Dual-Firewall Invariant
**Propósito:** Neutralizar la ceguera de auto-consistencia en modelos de lenguaje mediante arbitraje dual de Entropía Semántica y Oráculos SMT en silicio.
**Mecánica:**
- Todo cálculo de incertidumbre epistémica sobre realizaciones estocásticas $N \le 8$ DEBE ejecutarse en `#![no_std]` sin operaciones de punto flotante (`ENTROPY_LUT_Q16`), empaquetando el grafo de equivalencia en un `u64`.
- **Apoptosis Determinista:** La dispersión térmica estocástica ($H_{\text{sem}} > \tau$) detona `0xDEAD_6060` (Confabulación). Toda afirmación con $H_{\text{sem}} \le \tau$ que viole las restricciones formales de Ring-0 detona `0xDEAD_6061` (Creencia Errónea Sistemática).
- Queda terminantemente prohibido validar claims basándose exclusivamente en la convergencia interna de la inferencia autorregresiva.

---


## 2. Invariantes de la Máquina Abstracta (Semántica Operacional)

Adicionalmente a los invariantes arquitectónicos, la máquina abstracta F60 impone cinco invariantes estructurales sobre su memoria y ejecución:

- **I1 (Unicidad Operacional):** Ninguna corrutina ejecuta más de una instrucción por escalar de tiempo `UNIT.TICK`.
- **I2 (Causalidad Única):** Cada evento de mutación posee una firma criptográfica única.
- **I3 (Inmutabilidad del Pasado):** El DAG Causal (`Ledger`) es estrictamente *append-only*. Ningún registro puede ser mutado retrospectivamente.
- **I4 (Monotonicidad Temporal):** El reloj de la máquina siempre avanza, es decir, $C.\text{now}() \le C.\text{next}()$.
- **I5 (Ausencia de Anergía):** Toda mutación es computacionalmente reversible o trazable (transparente en su memoria inmutable, su tipo lineal o el registro del Ledger).