# ADR-003: Arquitectura BFT y Modelo de Atestación Criptográfica

![Status: C5-REAL](https://img.shields.io/badge/Status-C5--REAL-black?style=flat-square&logo=rust&logoColor=white)


- **Estado:** Aceptada
- **Fecha:** 2026-08-08
- **Autor:** Borja Moskv (borjamoskv)

## Contexto

BABYLON-60 necesita un mecanismo de consenso para garantizar la integridad causal de las transiciones de estado en un entorno multi-agente donde:
- Múltiples agentes IA pueden proponer mutaciones al estado global.
- La trazabilidad (provenance) de cada decisión debe ser criptográficamente verificable.
- El sistema debe tolerar agentes maliciosos o alucinantes sin comprometer la integridad del ledger.

## Decisión

Se implementa un **protocolo BFT (Byzantine Fault Tolerance)** basado en HotStuff con **atestación criptográfica por hash registry** para cada transición de estado.

## Justificación

### ¿Por qué BFT y no Raft/Paxos?

| Criterio | Raft/Paxos | BFT (HotStuff) |
|---|---|---|
| Modelo de fallo | Crash-fault (nodos honestos que caen) | Byzantine-fault (nodos que mienten) |
| Agentes IA | No cubre alucinación | Cubre respuestas arbitrarias |
| Complejidad de comunicación | O(n) | O(n) (HotStuff lineal) |
| Aplicabilidad a AI Safety | Insuficiente | Adecuada |

Los agentes IA, por naturaleza, pueden producir outputs arbitrarios (alucinaciones = fallo bizantino). Un protocolo crash-fault asumiría que los agentes son honestos-pero-falibles, lo cual es una premisa incorrecta para AI Safety.

### Modelo de atestación

Cada transición de estado `S₁ → S₂` produce un **attestation record**:

```
Attestation = {
    state_hash: SHA-256(S₂),
    parent_hash: SHA-256(S₁),
    agent_id: Ed25519_pubkey,
    signature: Ed25519_sign(state_hash || parent_hash || timestamp),
    timestamp: LogicalClock.tick
}
```

Esto crea una cadena Merkle de transiciones donde:
- Cada estado referencia criptográficamente a su predecesor causal.
- La firma del agente permite auditar quién propuso cada mutación.
- El reloj lógico desacopla la causalidad del tiempo físico (CALM theorem).

### Implementación

- `packages/babylon60/bft/` — Motor de consenso en Python.
- `packages/babylon60/attestation/` — Generación y verificación de attestation records.
- `packages/babylon60/crypto/hash_registry.py` — Registro canónico de hashes.
- `crates/strike-rs/` — Motor de consenso de alto rendimiento en Rust.
- `tests/test_hotstuff_consensus.py`, `test_raft_consensus.py` — Suite de validación.

## Consecuencias

- **Positivas:** Inmunidad verificable contra inyección causal (prompt injection). Auditoría post-mortem criptográfica de toda decisión. Alineado con EU AI Act Art. 12 (trazabilidad).
- **Negativas:** Overhead de latencia por firma criptográfica en cada transición (~1-5ms por Ed25519 sign). Mayor complejidad de implementación vs Raft simple.
- **Riesgo:** En configuraciones de agente único (Bus Factor = 1), el BFT no aporta tolerancia a fallos real (requiere f+1 nodos). Mitigación: el valor primario es la cadena de atestación, no la tolerancia distribuida.

## Referencias

- Yin et al. (2019): "HotStuff: BFT Consensus with Linearity and Responsiveness"
- Fischer, Lynch, Paterson (1985): FLP Impossibility
- EU AI Act, Artículo 12: Trazabilidad y logging
