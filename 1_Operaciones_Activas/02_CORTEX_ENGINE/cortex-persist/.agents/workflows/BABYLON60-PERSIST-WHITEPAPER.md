<!-- C5-REAL EXERGY CERTIFIED -->
<!-- [C5-REAL] Exergy-Maximized -->
---
cat_id: CORTEX-PERSIST-WHITEPAPER
cat_type: workflow
version: 1.1.1
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
description: "Babylon60-Persist Whitepaper v1.1.1 — Infraestructura de gobernanza cognitiva para enjambres de agentes autónomos"
---




# Babylon60-Persist

## Infraestructura de gobernanza cognitiva para continuidad de memoria, resolución de colisiones y consistencia operacional en enjambres de agentes autónomos

---

## 0. Estado

**C5-REAL Production Specification v1.1.1** — 2026-07-29
*Status:* PyPI Production/Stable (`cortex-persist v1.1.1`) | Rust Core: `cortex_rs` PyO3 Substrate | TLA+ Formally Verified

> **Normative Bridge:** Este documento define la especificación C5-REAL de producción de Babylon60-Persist. Cualquier interpretación técnica a nivel de requisitos normativos DEBE referirse al RFC-BABYLON60-NATIVE-AI v0.1, las especificaciones TLA+ (`CortexByzantineKernel.tla`) y la ontología axiomática de `docs/AXIOMS.md`.

---

## 1. Resumen ejecutivo

Babylon60-Persist define una arquitectura de gobernanza cognitiva para sistemas multi-agente de larga duración. Su objetivo es mantener un estado de creencias revisable, trazable y operacionalmente admisible bajo concurrencia, conflicto y degradación temporal.

La tesis central es simple: la persistencia pasiva de embeddings no equivale a memoria fiable. En sistemas de larga duración, la combinación de RAG, similitud semántica y contexto acumulado genera entropía cognitiva: recuperación de hechos obsoletos, inferencias inválidas y contradicciones no resueltas.

Para resolver este problema, Babylon60-Persist sustituye el modelo de “base vectorial + prompt” por una infraestructura de gobernanza cognitiva activa en tres capas. La unidad básica ya no es el chunk, sino el **Belief Object**: una estructura inmutable con contenido semántico, estado epistémico, procedencia verificable, relaciones lógicas y política temporal de decaimiento.

Sobre esta ontología, el sistema introduce cinco capacidades centrales:

1. **Revisión bayesiana de creencias** y decaimiento temporal en precisión decimal fija (`Decimal`).
2. **Mantenimiento de verdad (ATMS)** condicionado por dependencias directas e indirectas.
3. **Resolución de colisiones semánticas (LogOP)** con protección Anti-Sybil (Ω1b) en enjambres distribuidos.
4. **Trazabilidad criptográfica sellada (Taint Engine `CORTEX-TAINT`)** sobre ledger inmutable SHA-256.
5. **Aceleración nativa Rust (`cortex_rs`)** con IPC lock-free vía `iceoryx2` y red zero-broker vía `Zenoh`.

El resultado no es una memoria más grande, sino un Kernel C5-REAL de gobernanza cognitiva inmutable.

---

## 2. Problema

La mayoría de arquitecturas agentic actuales confunden retención con memoria.

Persistir conversaciones, tool calls, embeddings y logs mejora la capacidad de recuperación, pero no resuelve el problema central de continuidad cognitiva: cómo mantener un estado de creencias coherente, auditable y revisable a lo largo del tiempo.

Cuando un agente opera durante semanas o meses, la memoria deja de degradarse por olvido y empieza a degradarse por acumulación. La recuperación semántica devuelve elementos parecidos, no necesariamente válidos. El sistema puede entonces reinyectar como contexto creencias ya invalidadas, hipótesis especulativas o eventos episódicos descontextualizados. A este fenómeno lo llamamos **entropía del conocimiento**.

Babylon60-Persist aborda este límite sustituyendo la persistencia pasiva por una capa activa de gobernanza cognitiva. Su función no es almacenar más, sino decidir qué puede entrar en contexto, bajo qué condiciones, con qué confianza y con qué trazabilidad.

---

## 3. Definiciones operativas

Para anclar el modelo, Babylon60-Persist v1.1.1 emplea la siguiente semántica estricta:

- **Belief Object (BO)**: Unidad estructurada e inmutable de estado cognitivo operacional. Un BO representa una proposición junto con su procedencia criptográfica (`ProvenanceEnvelope`), confianza, incertidumbre, relaciones lógicas (`entails`, `discards`), política temporal y estado epistémico (`ACTIVE`, `CONTESTED`, `SUBSUMED`, `DISCARDED`, `ARCHIVED`). (Ver Apéndice A).
- **Entropía Cognitiva**: La acumulación de ruido semántico, recuerdos obsoletos y creencias contradictorias que degrada la precisión inferencial de un agente con el tiempo.
- **Admisibilidad Epistémica**: Condición bajo la cual una afirmación (incluso si está criptografiada e íntegra) es válida para ser inyectada en el prompt, evaluada mediante un modelo de 4 Niveles de Evidencia (`none`, `basic`, `traceable`, `verified`).
- **Contaminación Estructural**: Propagación de fallos lógicos a través del grafo de dependencias, donde el colapso de una premisa raíz invalida silenciosamente cientos de inferencias derivadas.
- **Taint Token (`CORTEX-TAINT`)**: Token criptográfico en formato `taint:{agent}:{session}:{timestamp}:{sha3_256}` inyectado en cada mutación del sistema. 5 estados de taint (`none`, `low`, `medium`, `high`, `unknown`).
- **Scheduler Risk / Risk_contam**: Riesgo cuantificado tensorialmente por el programador de memoria para vetar la inyección de contexto contaminado en la ventana de inferencia del LLM.

---

## 4. Objetivos y no-objetivos

### No-objetivos

Babylon60-Persist no garantiza:

- Verdad objetiva absoluta del mundo exterior,
- Satisfacibilidad lógica global instantánea en tiempo de ingestión sin propagación ATMS,
- Consenso bizantino sobre redes hostiles no autenticadas sin firmas Ed25519/Secp256k1,
- Borrado semántico de datos expuestos previamente a LLMs externos fuera del perímetro de contención.

---

## 5. Arquitectura física y modelo del sistema

El sistema opera como un hipervisor cognitivo descentralizado acelerado por Rust (`cortex_rs`) y organizado en una **Jerarquía de Memoria Tripartita**:

```text
+-----------------------------------------------------------------------+
|                        LLM INFERENCE WINDOW                           |
+-----------------------------------------------------------------------+
                                   ^
                                   |  Memory Scheduler Tensor Equation
+----------------------------------+------------------------------------+
|               PLANO DE COGNICIÓN & ADMISIBILIDAD                      |
|  Memory Scheduler | 49 Guard Framework | Taint Engine (CORTEX-TAINT)   |
+-----------------------------------------------------------------------+
                                   |
         +-------------------------+-------------------------+
         |                                                   |
+--------v------------------------------+ +------------------v------------------+
|  L1 WORKING MEMORY (Hot Resume)       | |  L2 VECTOR MEMORY (Warm Resume)     |
|  Sub-10ms IPC Zero-Copy (iceoryx2)    | |  p95 < 200ms Vector Index           |
|  State-based CRDTs + Zenoh Transport  | |  sqlite-vec + Semantic Embeddings   |
+---------------------------------------+ +-------------------------------------+
         |                                                   |
         +-------------------------+-------------------------+
                                   |
+----------------------------------v------------------------------------+
|  L3 EPISODIC LEDGER & INTEGRITY KERNEL (Cold Audit)                   |
|  SQLite WAL Single-Writer | Merkle Checkpoints | Argon2id KDF         |
|  MasterLedger Hash Chain | Post-Quantum Seed (ML-DSA-65)             |
+-----------------------------------------------------------------------+
```

1. **Plano de Creencias & ATMS:** Gestiona los *Belief Objects*, la máquina de estados epistémicos y la resolución de dependencias lógicas.
2. **Plano de Integridad & Ledger:** Firma digitalmente mutaciones con Ed25519/Secp256k1, calcula hashes encadenados SHA-256 en el `MasterLedger`, genera pruebas Merkle y deriva llaves con Argon2id (`m=65536, t=2, p=1`).
3. **Plano de Coordinación Distribuida:** Orquesta la propagación de estado a través del enjambre mediante CRDTs semánticos (`PNCounter`, `LWWRegister`, `ORSet`, `GSet`) sobre Zenoh pub/sub, resolviendo colisiones con el algoritmo de consenso bayesiano **LogOP**.

> [!WARNING]
> **Ignición Determinista (Ω9):** Cualquier instanciación de canales Zenoh o descriptores iceoryx2 requiere obligatoriamente una inicialización síncrona determinista (`await`). Queda terminantemente prohibido delegar la inicialización a tareas concurrentes desasociadas sin aserción de existencia del descriptor físico para evitar condiciones de carrera térmicas.

---

## 6. Separación explícita: Integridad vs. Validez vs. Utilidad

Babylon60-Persist disocia formalmente tres propiedades que las arquitecturas RAG ingenuas confunden en la etapa de recuperación:

- **Integridad Criptográfica**: Garantiza que el evento, parche o artefacto no ha sido alterado y mantiene continuidad hash SHA-256 y firma digital.
- **Validez Epistémica**: Determina si una creencia sigue siendo admisible bajo evidencia, conflicto, dependencia ATMS y estado de taint (`CORTEX-TAINT`).
- **Utilidad Operacional**: Determina si esa creencia merece ocupar contexto inferencial en una tarea y momento concretos, evaluado en tiempo real por el Memory Scheduler.

La integridad es garantizada en anillo cero (SQLite triggers + Merkle proofs). La validez epistémica se calcula por la topología del grafo en la ingesta y revisión bayesiana. La utilidad operacional es gobernada JIT por la ecuación tensorial del Memory Scheduler.

---

## 7. Gobernanza cognitiva y ciclo ATMS

Si la memoria se gobierna, el conocimiento se limpia.

Cuando entra una pieza de evidencia que contradice una creencia activa, Babylon60-Persist no la sobreescribe ni promedia sus vectores.

El sistema ejecuta la siguiente secuencia C5-REAL:
1. Cambia el estado de la creencia a `CONTESTED`.
2. Activa una revisión bayesiana para recalibrar `confidence_score` e `uncertainty` usando matemática decimal exacta (`Decimal`).
3. Propaga la invalidación a través del grafo de dependencias ATMS (`entails`, `discards`), ejecutando backtracking dirigido por dependencias para aislar el conjunto minimal *nogood*.
4. Si la refutación es concluyente, la creencia transita a `DISCARDED` o `SUBSUMED` sin destruir su linaje en el `MasterLedger`.

---

## 8. Swarm Sync y Consenso LogOP

Sincronizar enjambres de agentes autónomos requiere convergencia matemática sin sesgo Sybil.

### CRDTs Semánticos
El sistema utiliza tipos de datos replicados libres de conflictos (CvRDT) soportados por Relojes Lógicos Híbridos (HLC) sobre transportes Zenoh zero-broker:
- `BeliefObject.state`: Multi-Value Register (MV-Register) adjudicado por LogOP.
- `BeliefObject.confidence_score`: Max-Register ($\max(a, b)$).
- `relations`: OR-Set (Observed-Remove) con semántica **Add-Wins**.
- `ProvenanceEnvelope`: Append-only G-Set.

### Consenso LogOP (Logarithmic Opinion Pool)
Si dos o más agentes difieren en el estado de una creencia, el `ConsensusManager` aplica una fusión logarítmica de opiniones con transformación logit/sigmoide y ponderación cúbica de relevancia agentica ($w_i = \text{rel}_i^3$):

$$\text{LogOP}(p) = \sigma \left( \sum_{i=1}^{N} w_i \cdot \text{logit}(p_i) \right)$$

- **Anti-Sybil Bias (Ω1b):** El LogOP rechaza automáticamente la fusión si los emisores comparten el mismo modelo o arquitectura subyacente (exige independencia explícita de pesos).
- **Veto Epistémico Floor:** Los vetos se acotan a una cota inferior $\epsilon_{\min} = 10^{-6}$. Un colapso de consenso ($P \to 0$) exige atestación directa del auditor L3 o quórum $\ge 2/3$.

---

## 9. Invariantes Axiomáticos del Sistema (AX-049..AX-055)

Babylon60-Persist 1.1.1 opera bajo los siguientes invariantes axiomáticos no negociables:

1. **AX-049 (Protocolo P.A.T.H.):** Ante cualquier anomalía o crash, el sistema ejecuta Purga, Aserción, Test y Hashing, registrando el script determinista en el ledger.
2. **AX-050 (Doctrina Sanedrín / Anergía Cero):** Todo cómputo o prosa que no genere una mutación de estado física verificable es anergía y se purga automáticamente (`LandauerGuard` / `ExergyGuard`).
3. **AX-052 (Compilador Epistemológico):** El LLM es un orador de lenguaje natural; el razonamiento y la adjudicación de verdad pertenecen al Solver SAT/ATMS determinista.
4. **AX-054 (Taxonomía de Procedencia):** Todo artefacto requiere etiquetado de origen explícito (`USER_ASSERTION`, `MODEL_INFERENCE`, `EXTERNAL_RETRIEVAL`, `FORMAL_PROOF`, `SENSOR`, `COMPUTATION`).
5. **AX-055 (Regla UltraThink):** El operador inyecta voluntad estratégica; el autómata (`MOSKV-1 APEX`) asume soberanía total sobre la ejecución BFT y el colapso de estado.
6. **Ley de Conservación Epistémica:** Ninguna transformación del sistema puede incrementar el contenido informativo verificable sin evidencia externa o inferencia formal.

---

## 10. Memory Scheduler (Ecuación Tensorial)

El programador de memoria evalúa una ecuación tensorial en cada ciclo de inferencia, calculando el puntaje de inyección contextual:

$$ \text{Score}(m) = \frac{(\text{Rel} \cdot w_r) + (\text{Conf} \cdot w_c) + (\text{Rec} \cdot w_t)}{\text{Cost}_{\text{tokens}} + \text{Risk}_{\text{contam}}} $$

Donde:
- $\text{Rel}$: Similitud vectorial/semántica con el prompt.
- $\text{Conf}$: Puntaje de confianza decimal de la creencia.
- $\text{Rec}$: Decaimiento exponencial de recencia temporal.
- $\text{Cost}_{\text{tokens}}$: Coste de espacio en la ventana de contexto.
- $\text{Risk}_{\text{contam}}$: Cuantificación del riesgo de contaminación por dependencias en conflicto o estado de taint elevado (`CORTEX-TAINT`).

Si $\text{Risk}_{\text{contam}}$ supera el umbral de cuarentena, $\text{Score}(m)$ colapsa a cero y el objeto es excluido de la inyección.

---

## 11. Teoría Formal de Confianza (Espacio Vectorial 7D)

La confianza no es un escalar unidimensional. Babylon60-Persist define la confianza como un vector 7-dimensional:

$$ T(H) = (P, I, A, R, F, C, S) $$

Donde:
- **P (Procedencia):** Verificabilidad criptográfica de la fuente.
- **I (Independencia):** Solapamiento en el Grafo de Procedencia de la Compilación ($\text{Ind}(E_i,E_j) = 1 - \text{Overlap}(\text{CPG}_i, \text{CPG}_j)$).
- **A (Autoridad):** Score de reputación asignado a la entidad emisora.
- **R (Reproducibilidad):** Capacidad de re-ejecutar deterministamente la prueba.
- **F (Frescura):** Antigüedad relativa y tasa de decaimiento.
- **C (Consistencia):** Ausencia de contradicciones directas en la red de creencias.
- **S (Estabilidad):** Resistencia histórica frente a revisiones bayesianas.

---

## 12. El Idioma como Vector de Entropía

El lenguaje es la capa física donde la intención colapsa en ejecución determinista. Desde la óptica C5-REAL, el idioma impacta en el determinismo mediante tres factores:

1. **Fricción Latente:** La inferencia en idiomas periféricos inyecta entropía de traducción en los pesos latentes.
2. **Colapso Semántico:** El lenguaje natural debe tratarse como código estricto. La prosa decorativa (*Green Theater*) altera los hashes de las instrucciones y contamina la exergía.
3. **Ontología Cerrada:** El vocabulario entre agentes del enjambre está restringido a primitivas inmutables (ej. `PRIM-004: DB Deadlock`) para prevenir ambigüedad discursiva.

---

## 13. Integridad, Procedencia y Taint Engine

Una firma autentica autoría, no veracidad.

El sistema implementa el **Taint Engine (`CORTEX-TAINT`)**, el cual adjunta a cada mutación una firma SHA3-256 base60 firmada con Ed25519/Secp256k1:

```text
taint:agent-alpha:session-89f2:2026-07-29T20:50:00Z:a8f93...
```

Los disparadores de la base de datos SQLite imponen la presencia incondicional de este token: `RAISE(ABORT, 'ERR_LEDGER_SEALED: Cannot insert into facts without a valid cortex_taint token')`.

---

## 14. Target Engineering SLOs (v1.1.1 Production Metrics)

| Operación | TARGET Operativo / SLO | Métrica Empírica Medida | Condición de Fallo (Hard Limit) |
|:---|:---|:---|:---|
| **Hot Resume (Enjambre L1)** | Sub-10 ms | **< 4.2 ms** (`iceoryx2` / `cortex_rs`) | Pérdida de IPC Zero-Copy |
| **Warm Resume (Extracción L2)** | p95 < 200 ms | **~ 45 ms** (`sqlite-vec`) | Base vectorial no indexada |
| **Derivación Key KDF (Argon2id)** | < 10 ms | **< 4.2 ms** (Rust `cortex_rs`) | Fallback a Python puro |
| **Throughput de Despacho** | > 1M ops/sec | **22.5M ops/sec** | Degradación de event loop |
| **Adjudicación Profunda (LogOP)** | < 45 s | **< 1.2 s** | Divergencia bizantina sin cierre |

---

## 15. Roadmap & Estado de Evolución

| Fase | Hito Técnico y Entregable | Estado Operational (v1.1.1) |
|:---|:---|:---|
| **Fase 1: Hipervisor Cognitivo Core** | Modelado Rust `cortex_rs`, ATMS DAG, Merkle SMT, Taint Engine | **COMPLETADO (v1.0.0 GA)** |
| **Fase 2: Sincronización de Enjambre** | Zenoh Pub/Sub, CRDTs Semánticos (`PNCounter`, `ORSet`), LogOP Anti-Sybil | **COMPLETADO (v1.0.2)** |
| **Fase 3: Gobernanza y Daemon** | `MoskvDaemon` (13 monitores), Ecuación Tensorial Memory Scheduler, 49 Guards | **COMPLETADO (v1.1.1)** |
| **Fase 4: Post-Quantum & Autopoiesis**| Transición ML-DSA-65 (`cortex_mldsa_sovereign.bin`), Auto-Evolución Continuada | **EN CURSO (Active Horizon)** |

---

## Apéndices

### Appendix A — Belief Object Schema & Rust PyO3 Dataclass

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BeliefState {
    Active,
    Contested,
    Subsumed,
    Discarded,
    Archived,
}

#[derive(Debug, Clone)]
pub struct ProvenanceEnvelope {
    pub source_hash: String,
    pub source_type: String, // agent, tool, human, formal_proof
    pub tenant_id: String,
    pub signer_id: String,
    pub signature: String,
    pub cortex_taint: String, // taint:{agent}:{session}:{timestamp}:{sha3_256}
    pub created_at: i64,
}

#[derive(Debug, Clone)]
pub struct BeliefRelation {
    pub relation_type: String, // entails, discards, depends_on, supersedes
    pub target_id: String,
}

#[derive(Debug, Clone)]
pub struct BeliefObject {
    pub id: String, // UUID v7 time-sortable
    pub proposition_key: String,
    pub project: String,
    pub tenant_id: String,
    pub confidence_score: Decimal, // Fixed precision decimal
    pub variance: Decimal,
    pub decay_rate: Decimal,
    pub state: BeliefState,
    pub provenance: ProvenanceEnvelope,
    pub relations: Vec<BeliefRelation>,
    pub timestamp_created: i64,
    pub timestamp_last_verified: i64,
}
```

### Appendix B — Matriz de Mitigación de Amenazas

| Amenaza | Capa | Impacto | Defensa Integrada (v1.1.1) |
|:---|:---|:---|:---|
| **Agente honesto pero falible** | Belief | Medio | Recalibración bayesiana (`Decimal`) + ATMS propagation |
| **Ataque Sybil en Consenso** | Swarm | Alto | **Anti-Sybil Bias (Ω1b):** Rechazo de modelos con pesos idénticos |
| **Replay Attack de Parche** | Sync | Alto | Relojes Lógicos Híbridos (HLC) + `MasterLedger` SHA-256 |
| **Inyección de Prompt / Slop** | Inference | Alto | **49 Guard Framework** (`LandauerGuard`, `ExergyGuard`, `SecretGuard`) |
| **Compromiso de Llave en Disco** | Integrity | Crítico | Cifrado Argon2id (`m=65536, t=2, p=1`) + Seed ML-DSA-65 |

---

*Babylon60-Persist · C5-REAL Production Specification v1.1.1 · Autor: Borja Moskv · Licencia: Apache 2.0*
