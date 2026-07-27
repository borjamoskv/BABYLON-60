<!-- [C5-REAL] Exergy-Maximized -->
# CEP-001: Core Kernel Contracts

* Id: CEP-001
* Título: Contratos Mínimos del Núcleo y Modelo de Persistencia Epistémica
* Estado: Borrador Integrado (Draft)
* Ámbito: Arquitectura del Microkernel
* Fecha: Junio 2026

------------------------------
## 1. Principios Fundamentales de Diseño
La arquitectura BABYLON-60 se rige por tres invariantes de diseño que delimitan de forma estricta las responsabilidades del núcleo del sistema:

1. Estabilidad de Interfaces: Las interfaces deben estabilizarse antes que los algoritmos que las implementan. El éxito técnico del núcleo consiste en garantizar que la evolución del conocimiento (nuevas teorías de confianza, motores de inferencia o solvers) no implique la reescritura de la arquitectura.
2. Agnosticismo Semántico: El microkernel nunca interpreta el significado de los objetos que almacena. Únicamente garantiza su identidad, integridad, trazabilidad y compatibilidad estructural. El núcleo no determina si una afirmación es verdadera; solo valida si está bien formada y si cumple con los contratos.
3. Neutralidad Epistemológica del Núcleo: El microkernel no implementa ninguna teoría de la verdad, de la confianza ni de la inferencia. Su única responsabilidad es garantizar que cualquier teoría compatible con los contratos del sistema pueda persistir, evolucionar y ser auditada sin comprometer la integridad estructural del repositorio epistémico. Bajo este principio, la "verdad" deja de ser un estado privilegiado: el núcleo puede almacenar hipótesis, contradicciones, múltiples valoraciones incompatibles y ramas alternativas del conocimiento de forma simultánea.

------------------------------
## 2. Core Object Model (EpistemicObject)
Todos los objetos que transitan por el núcleo de BABYLON-60 heredan de la interfaz abstracta EpistemicObject. Son estructuras de datos puras, estáticas, inmutables y serializables de forma determinista. Carecen de lógica de ejecución interna.

```text
EpistemicObject (Abstract)
 ├── id: UIDv7 / URI (Identidad única con orden temporal implícito)
 └── hash: SHA-256 (Huella digital calculada a partir de la estructura del objeto)
```

### 2.1 Assertion
Representa una proposición atómica sobre el dominio de discurso.

* Restricción Crítica: Está estrictamente prohibido que contenga metadatos sobre certeza, probabilidad, confianza, fuentes o pesos numéricos. La aserción es semántica pura.
* Campos Obligatorios:
  * id: Identificador único.
  * subject: Entidad u objeto de la declaración (URI/ID).
  * predicate: Relación, propiedad o verbo de la aserción.
  * object: Valor, entidad destino o término de la relación.
  * context: Ámbito de validez semántica o namespace de la proposición.
* Invariante: Dos instancias de Assertion con idéntico sujeto, predicado, objeto y contexto generan el mismo hash estructural y representan conceptualmente la misma aserción.

### 2.2 Evidence
Representa un artefacto observable y verificable extraído del mundo exterior o del sistema histórico. No contiene la lógica de su interpretación.

* Campos Obligatorios:
  * id: Identificador único.
  * evidence_type: Clasificación formal del artefacto (ej. LOG_ENTRY, CRYPTOGRAPHIC_PROOF, SENSOR_READING).
  * payload_reference: URI o hash criptográfico externo al kernel que apunta al dato crudo de la prueba.
* Invariante: La mutación del artefacto externo referenciado no altera el objeto Evidence. Cualquier cambio en el origen exige instanciar un objeto independiente con una nueva referencia.

### 2.3 SupportRelation
Formaliza la topología del grafo epistémico. Extrae las relaciones fuera de los nodos de datos puros, permitiendo que la interpretación de las pruebas sea un elemento dinámico e independiente.

* Campos Obligatorios:
  * id: Identificador único.
  * evidence_id: ID del objeto Evidence de origen.
  * assertion_id: ID del objeto Assertion de destino.
  * relation_type: Enum formal con la semántica del enlace:
  `relation_type ∈ { SUPPORTS, REFUTES, OBSERVES, DERIVED_FROM, CONTRADICTS }`
* Invariante: Un cambio en la interpretación de una prueba no muta las entidades Assertion ni Evidence. Simplemente genera o elimina objetos SupportRelation en el estado.

### 2.4 Provenance
Captura metadatos obligatorios de autoría, causalidad y temporalidad de la creación de cualquier objeto del sistema.

* Campos Obligatorios:
  * id: Identificador único.
  * actor: Entidad (agente, clave pública o subsistema) que generó el objeto.
  * timestamp: Marca de tiempo de alta precisión, linealizada y conforme al reloj del sistema.
  * cause: ID del objeto o regla previa que gatilló esta creación (opcional, para trazabilidad causal).

### 2.5 Constraint
Define las fronteras de coherencia lógica o las reglas de integridad que el dominio no puede violar.

* Campos Obligatorios:
  * id: Identificador único.
  * scope: Lista de tipos o contextos de aserción sobre los que aplica.
  * expression: Declaración formal de la restricción en sintaxis abstracta.

### 2.6 Diagnostic
Metadato estructural que describe anomalías, contradicciones lógicas o violaciones de restricciones detectadas en un estado concreto.

* Campos Obligatorios:
  * id: Identificador único.
  * severity: Grado de quiebre (INFO, WARNING, CONTRADICTION, CRITICAL_VIOLATION).
  * affected_objects: Lista de IDs involucrados en la anomalía.
  * description: Estructura tipificada con el reporte del error.

------------------------------
## 3. Core State Model (EpistemicState)
El EpistemicState es una instantánea (Snapshot) inmutable e indexada de un conjunto consistente de objetos epistemológicos y de las relaciones existentes entre ellos. No almacena datos de forma directa; funciona exclusivamente mediante punteros y tablas de referencias referenciadas por hashcriptográfico.

### 3.1 Estructura del Estado
```text
EpistemicState
 ├── state_id: UIDv7
 ├── parent_states: List<StateID> (Permite bifurcaciones, paralelismo e historias multilineales)
 ├── merkle_root: Hash (Raíz criptográfica calculada de forma incremental)
 ├── provenances: HashSet<ProvenanceID>
 │
 ├── INDEXES (Colección de referencias a objetos persistidos)
 │    ├── assertion_index: HashSet<AssertionID>
 │    ├── evidence_index: HashSet<EvidenceID>
 │    ├── relation_index: HashSet<RelationID>
 │    ├── constraint_index: HashSet<ConstraintID>
 │    └── diagnostic_index: HashSet<DiagnosticID>
 │
 └── epistemic_valuations: Map<AssertionID, TrustValue>
```

* Invariante de Tasación: El TrustValue mapeado a cada aserción es una estructura opaca para el microkernel. El núcleo no sabe calcularlo ni interpretarlo; solo garantiza su almacenamiento inalterable dentro del mapa del estado.

### 3.2 Identidad del Estado mediante Merkle Root
La integridad del estado se autoverifica de forma incremental estructurando sus índices como un árbol de Merkle. El merkle_root global es el hash resultante de la combinación de las raíces de los sub-árboles de cada índice independiente:

```text
                  [ EpistemicState Merkle Root ]
                                / \
                               /   \
                              /     \
             [ Data Subtree Root ]   [ Graph Subtree Root ]
                    /      \                 /         \
         assertions_h  evidences_h     relations_h  valuations_h
```

Esta topología permite:
* Auditoría Incremental: Las transiciones parciales solo recalculan las ramas modificadas en tiempo $O(\log N)$, reutilizando el resto de sub-árboles intactos del estado padre.
* Pruebas de Inclusión (Merkle Proofs): Sistemas externos pueden certificar la pertenencia de una aserción a un estado legítimo aportando únicamente la rama criptográfica correspondiente, sin exponer el contenido completo del snapshot.

------------------------------
## 4. Epistemic Commit Protocol
El ciclo de vida de la información diferencia de manera radical el estado propuesto por un servicio externo del estado consolidado y certificado por el microkernel. Las modificaciones de la historia se realizan mediante una función de transición pura de tipo append-only:
`Transition(S_0, S_1, ..., S_n) -> S_{n+1}`

```text
  [Kernel Provider Driver] ──► Somete: ProposedState
                                     │
                                     ▼
                        ┌──────────────────────────┐
                        │   VALIDACIÓN DEL KERNEL  │
                        └────────────┬─────────────┘
                                     │
                        ┌────────────┴────────────┐
                  ¿Estructura OK?           ¿Fallo Estructural?
                        │                         │
                        ▼                         ▼
                 [CommittedState]          [Kernel Panic / Abort]
```

### 4.1 Anatomía del Commit
```text
EpistemicCommit
 ├── commit_id: UIDv7
 ├── parent_commits: List<CommitID>
 ├── proposed_state: ProposedState
 ├── commit_type: Enum { LOGICAL, VALUATED }
 └── signature: CryptographicSignature (Firma digital del proveedor que propone el cambio)
```

### 4.2 Contrato de Admisión del Microkernel
Al recibir una propuesta de commit, el núcleo ejecuta de forma estricta las siguientes verificaciones estructurales. Cualquier fallo aborta la operación inmediatamente:

1. Integridad de Tipos y Hashes: Comprueba que todos los objetos heredan de tipos válidos y que sus hashes estructurales coinciden exactamente con los calculados.
2. Inmutabilidad de Registro: Si un objeto ya existía en un commit previo del historial de la rama, su estructura física debe ser idéntica. No se permite alterar datos históricos.
3. Resolución de Referencias (Dangling References): Cada ID de objeto referenciado en los índices de relaciones (SupportRelation) o tasaciones debe existir en el espacio de datos del estado propuesto o en sus ancestros.
4. Integridad del DAG Histórico: Valida que los parent_commits apuntan a nodos preexistentes en el repositorio y comprueba, mediante ordenamiento topológico, que la transición no genera dependencias circulares en la línea de tiempo.

### 4.3 Clasificación del Compromiso: Dos Niveles de Registro
El microkernel delega el análisis semántico y la valoración numérica separando la consolidación en dos fases:

* Logical Commit: Certifica exclusivamente que los objetos, los tipos, las relaciones y las propiedades criptográficas del estado propuesto son estructuralmente válidos. El estado es apto para su almacenamiento y persistencia en el DAG histórico. El mapa epistemic_valuations puede estar vacío.
* Valuated Commit: Requiere la intervención y firma de un proveedor externo de confianza (KSI-TrustProvider). Certifica que el mapa epistemic_valuations ha sido calculado y anotado de forma completa sobre el estado, aplicando un álgebra de confianza específica sin alterar la base estructural previa.

------------------------------
## 5. Kernel Provider Interfaces (KPI)
Los componentes ejecutables externos actúan como drivers del sistema operativo. Interactúan con el microkernel exclusivamente a través de los contratos de las Kernel Provider Interfaces (KPI), garantizando el aislamiento absoluto entre el almacenamiento y el razonamiento:

* KPI-InferenceProvider: Lee snapshots en estado CommittedState, evalúa sus reglas internas y somete un nuevo ProposedState para generar un Logical Commit.
* KPI-TrustProvider: Toma un estado con un Logical Commit, calcula las dependencias y el mapa de pesos de las aserciones, y devuelve un ProposedState listo para ser consolidado como un Valuated Commit.
* KPI-ParserProvider / KPI-RendererProvider: Traducen flujos de datos externos hacia y desde las estructuras canónicas del Core Object Model.
