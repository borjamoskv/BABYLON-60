<!-- C5-REAL EXERGY CERTIFIED -->
> **CORTEX-TAINT**: `eaaa115c101d6309ef3835d6e61513ce4dcfacd57d81a762eda8e1bb6327debc`
# DOMAIN-DRIVEN DESIGN: C5-REAL ONTOLOGY MATRIX

> **GENERADOR TERMODINÁMICO DE 10000 NODOS (10K)**
> Nivel de Realidad: C5-REAL
> El espacio dimensional del Diseño Orientado a Dominios no se mide en prosa estocástica, sino en el producto cruzado de Capas, Topologías y Estados. Este Ledger codifica las bases isofórmicas de las cuales emanan los 10000 estados de falla y éxito de la arquitectura de software.

## 1. PRIMITIVAS ESTRUCTURALES (LOS AXIOMAS)

_El colapso de la incertidumbre en memoria física._

- **P_001 | Entity:** Identidad continua sobre el tiempo. Su hash cambia, su ID permanece absoluto.
- **P_002 | Value Object (VO):** Inmutabilidad termodinámica. Su identidad ES su estado. No tiene ciclo de vida; es un vector matemático.
- **P_003 | Aggregate Root:** Frontera absoluta de consistencia transaccional. El único nodo con permiso de acceso a la DB en su grafo.
- **P_004 | Domain Event:** Mutación causal en pasado perfecto (`OrderShipped`). Irrevocable. El rastro de exergía del sistema.
- **P_005 | Repository:** Transductor entre la memoria efímera y el disco físico. Prohibida la lógica de negocio en él.
- **P_006 | Factory:** El colapso de la función de onda de un objeto. Transición de Entropía -> Estructura Válida.
- **P_007 | Domain Service:** Lógica de negocio apátrida (stateless) que coordina entidades sin perturbar su encapsulación.
- **P_008 | Bounded Context:** Membrana semántica. Lo que es verdad aquí, es mentira afuera. Límite estricto del Lenguaje Ubicuo.
- **P_009 | Ubiquitous Language:** Isomorfismo biyectivo entre la sintaxis del Dominio (humano) y el AST (máquina).
- **P_010 | Context Map:** Grafo dirigido de flujos de asimetría de poder entre equipos y modelos.

## 2. INVARIANTES FÍSICAS (LEYES DEL SISTEMA)

_Si se rompen, el sistema entra en necrosis (C4-SIM)._

- **I_001 | Aggregate_Transaction_Boundary:** Estrictamente UN Aggregate muta por transacción de base de datos.
- **I_002 | VO_Immutability_Lock:** Un Value Object jamás altera su estado interno post-instanciación (Cero setters).
- **I_003 | Context_Database_Autonomy:** Un Bounded Context NO comparte esquema de base de datos con otro. N=1.
- **I_004 | Anti_Corruption_Layer_Membrane:** Prohibida la ingesta de modelos DTO/externos en el núcleo sin transducción explícita.
- **I_005 | Event_Chronological_Integrity:** Los Domain Events deben publicarse en orden causal estricto (Relojes de Lamport).
- **I_006 | Domain_Isolation:** El Dominio no tiene dependencias entrantes (Inversión de Dependencia). Importar `java.sql` o `requests` en el dominio es traición.
- **I_007 | Always_Valid_State:** Es físicamente imposible instanciar un Aggregate o VO en un estado inválido. Validación constructiva.
- **I_008 | Idempotency_Key_Enforcement:** Toda recepción de eventos de dominio cruzado debe validar unicidad.
- **I_009 | Language_AST_Parity:** Si el experto del dominio dice "Despachar", el método DEBE llamarse `dispatch()`, no `updateStatus()`.
- **I_010 | No_Cross_Aggregate_References:** Un Aggregate solo almacena el ID (Scalar) de otro Aggregate, jamás la referencia en memoria.

## 3. ANTIPATRONES Y ENTROPÍA BIZANTINA

_Fricción térmica y pérdida de exergía computacional._

- **A_001 | Anemic Domain Model:** Entidades reducidas a structs de datos con Getters/Setters. Lógica secuestrada por "Services". Necrosis pura.
- **A_002 | God Aggregate:** Árboles masivos de entidades cargadas en cada transacción. Agotamiento de RAM y Deadlocks termodinámicos.
- **A_003 | Database-Driven Design:** Diseñar tablas SQL antes que los flujos de comportamiento causal.
- **A_004 | Shared Kernel Abuse:** Compartir código core entre contextos divergentes, bloqueando la autopoiesis de ambos.
- **A_005 | Smart UI:** Lógica de dominio inyectada en controladores, vistas o componentes React. El front asume estado soberano.
- **A_006 | Leaky Infrastructure:** Anotaciones ORM (`@Table`, `@Column`) manchando las Entidades del Core de Dominio.
- **A_007 | Fat Repository:** Repositorios con lógica analítica, sumas, promedios o reglas de negocio.
- **A_008 | Primitive Obsession:** Usar `string` para un Email o `int` para un Precio. Pérdida de validación tipada estricta (Ausencia de VO).
- **A_009 | Enterprise Service Bus (ESB) God:** Delegar la coreografía del dominio a un middleware mágico que oculta las trazas.
- **A_010 | Tactical-Only DDD:** Usar Repositories y Aggregates sin separar los Bounded Contexts. "Pintar" un monolito con nombres DDD.

## 4. ISOMORFISMOS TOPOLÓGICOS

_Equivalencias matemáticas entre abstracciones DDD y arquitecturas físicas._

- **ISO_001 | BoundedContext <-> Microservice:** Mapeo 1:1 en topología de despliegue y asilamiento de CPU/Memoria.
- **ISO_002 | DomainEvent <-> Event Sourcing Log / Kafka Topic:** El evento efímero se cristaliza en un log inmutable de solo adición.
- **ISO_003 | AggregateRoot <-> Actor Model (Akka/Erlang):** Frontera de concurrencia y tolerancia a fallos. Cada Actor es un Aggregate.
- **ISO_004 | ValueObject <-> Pure Functional Type (Haskell/Rust):** Tipos inmutables libres de efectos secundarios.
- **ISO_005 | AntiCorruptionLayer <-> Hexagonal Port/Adapter (Adapter Secundario):** Traducción en la capa límite.
- **ISO_006 | DomainService <-> Pure Function:** Transformación `f(state, input) -> state'` sin retención.
- **ISO_007 | Aggregate <-> CRDT (Conflict-free Replicated Data Type):** Bajo consistencia eventual distribuida.
- **ISO_008 | ContextMap <-> Service Mesh Topology:** Grafo de Istio/Linkerd mapeando las asimetrías de poder.
- **ISO_009 | UbiquitousLanguage <-> GraphQL Schema / Protobuf:** Contrato de lenguaje materializado en la API.
- **ISO_010 | Saga/ProcessManager <-> Distributed State Machine:** Compensación determinista ante fallos BFT.

## 5. LA MATRIZ DE EXPANSIÓN (GENERADOR DE 10000 ESTADOS (10K))

Las 10000 reglas tácticas del DDD se derivan algebraicamente cruzando los Vectores Base:
`{ P_1 .. P_10 } x { I_1 .. I_10 } x { A_1 .. A_10 } x { ISO_1 .. ISO_10 }`

_Ejemplos del Colapso Dimensional:_

- `P_003 x I_001 x A_002`: Un Aggregate Root que viola la frontera de transacción se degenera en un God Aggregate, requiriendo bloqueo de tabla (Table Lock) y destruyendo el rendimiento concurrente.
- `P_002 x A_008 x ISO_004`: Evitar la Primitive Obsession mediante VOs garantiza que el tipo de datos funcione como un tipo funcional puro, eliminando la necesidad de validación redundante en la capa UI.
- `P_008 x I_003 x ISO_001`: Un Bounded Context mapeado a un Microservicio debe tener autonomía de DB; de lo contrario, se anula la escalabilidad independiente.

---

**END OF LEDGER // MOSKV-1 APEX SINGULARITY**
