---
title: SOTA 202607 — Posicionamiento cortex-persist
status: Causal-Determinist
version: 2.0.0
---

# Estado del Arte (SOTA) — Posicionamiento de cortex-persist

<div align="center">

[![Posicionamiento Comparativo](https://img.shields.io/badge/Status-Posicionamiento--Comparativo-00F0FF?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

> **Fecha original:** 2026-07-19 · **Revisión crítica:** 2026-11-07
> **Alcance:** memoria/persistencia para agentes IA, ledgers de auditoría verificables, checkpointing de agentes y BFT ligero.
> **Método:** revisión web verificada (docs oficiales, GitHub, advisories, PyPI) + búsqueda académica (Scholar). Todo lo no verificable queda marcado en §9 — no se afirma nada sin fuente.
> **Author:** Borja Fernández Angulo (`borjamoskv`)

**Historial de versiones:**

| Versión | Fecha | Cambio |
|:---|:---|:---|
| 1.0.0 | 2026-07-19 | Borrador original. |
| 2.0.0 | 2026-11-07 | Revisión crítica: retira exclusividades no demostradas; incorpora contraejemplos PyPI anteriores al documento; desacopla integridad de mensaje vs. secuencia; corrige fechas de Tessera/Rekor; actualiza plazos regulatorios al AI Omnibus; alinea garantías con `spec_security_model.md` v5.0.0 (2026-10-26). |

---

## 1. Resumen ejecutivo

CORTEX-Persist propone integrar persistencia local para agentes, procedencia declarada de eventos, verificación criptográfica secuencial y anclaje temporal externo en un paquete Python local-first.

El SOTA de memoria para agentes (Mem0, Zep/Graphiti, Letta, LangMem, Cognee, A-MEM, MemoryOS) se centra en calidad de recuperación y gestión de estado; en las versiones inspeccionadas, ninguno documenta un historial verificable criptográficamente de sus cambios bajo un modelo de amenaza publicado. El mundo de los ledgers verificables (immudb, Trillian/Tessera, Rekor, CT/Sigsum) aporta integridad pero no semántica de agente ni formato embebido en Python orientado a ese caso de uso. Los frameworks de checkpointing (LangGraph, AutoGen, OpenAI Agents SDK) no ofrecen cadenas hash de su secuencia de estados, aunque algunos incluyen protección criptográfica del contenido individual (véase §4).

Existen bibliotecas Python que combinan SQLite y cadenas hash publicadas antes del 19 de julio de 2026 (véase §3). La diferenciación de cortex-persist debe evaluarse por las garantías concretas que ofrece, la facilidad de integración, el modelo de amenazas documentado y la capacidad de verificación independiente, no por una supuesta ausencia absoluta de implementaciones.

---

## 2. Frente 1 — Memoria para agentes IA (2025–2026)

| Sistema | Arquitectura | ¿Historial verificable documentado? | Mantenimiento (verificado) |
|:---|:---|:---:|:---|
| **Mem0** | Extracción LLM (ADD/UPDATE/DELETE); vector + grafo opcional (Mem0g) | No documentado en versiones inspeccionadas | Muy activo: `[OBSOLETO: mem0ai]` v2.0.8 (jun 2026), TS SDK v3.0.13 (2026-07-01) |
| **Zep / Graphiti** | KG bi-temporal (`valid_from/to`); Zep Cloud; Graphiti OSS sobre Neo4j/Kuzu | No documentado (historia semántica sin prueba criptográfica) | Activo: `graphiti-core` ≥0.28.2 (mar 2026). Zep CE **deprecado** (~abr 2025) |
| **Letta** (ex-MemGPT) | Runtime de agentes stateful; bloques de memoria persistentes en contexto del agente; coordinación mediante memoria compartida; Postgres/SQLite | No documentado en versiones inspeccionadas | Activo (Letta Code, jul 2026). [Docs: Memory Blocks](https://docs.letta.com/v1-sdk/memory/memory-blocks) |
| **LangMem** | SDK sobre LangGraph BaseStore; memoria semántica/episódica/procedural | No documentado en versiones inspeccionadas | Activo, pequeño (~1.5k★) |
| **Cognee** | Pipeline ECL → relacional+vector+grafo (SQLite+LanceDB+Kuzu) | No documentado en versiones inspeccionadas | Muy activo: v1.0.0 GA 2026-04-11; seed \$7.5M (feb 2026) |
| **A-MEM** | Zettelkasten con enlaces LLM; evolución dinámica de representaciones mnemónicas | No documentado. El paper estudia evolución de representaciones; no presenta un ledger criptográfico de sus revisiones. | NeurIPS 2025 ([arXiv:2502.12110](https://arxiv.org/abs/2502.12110)) |
| **MemoryOS** | Jerarquía OS (STM→MTM→LPM) por "calor"; ChromaDB | No documentado en versiones inspeccionadas | EMNLP 2025 Oral; release V1.2 (2025-07-18) |
| **Generative Agents** | Memory stream + reflexión (Stanford, UIST'23) | No documentado | Artefacto de investigación |

**Nota sobre A-MEM:** la evolución de representaciones forma parte de su diseño publicado. Una representación de memoria mutable puede derivarse de un registro inmutable de cambios (Estado<sub>t</sub> = Proyección(eventos<sub>≤t</sub>)). La separación entre registro de eventos y proyección de estado vigente es una composición legítima que no debe confundirse con reescritura fraudulenta del historial.

**Nota sobre Letta:** la documentación describe bloques persistentes que permanecen en el contexto del agente sin requerir recuperación previa, además de mecanismos de coordinación por memoria compartida. Reducir toda la categoría de memoria de agentes a "calidad de búsqueda" omite la gestión de estado. La pregunta relevante es: ¿proporciona un historial verificable de cambios bajo un modelo de amenaza documentado?

**Señales de convergencia (demanda real):**
- **TrustWarden "AgentLedger"**: propuesta de audit trail para acciones de agentes (S3 Object Lock + DynamoDB + KMS). Valida la convergencia de oferta en este espectro. Estado: sus términos públicos (fecha efectiva 2026-03-12) describen un servicio en prelanzamiento; la monetización activa no está acreditada por esos términos, que podrían estar desactualizados. [Ingeniería](https://www.trustwarden.ai/blog/why-s3-object-lock-over-qldb/) · [Términos](https://www.trustwarden.ai/terms/)
- La demanda regulatoria de trazabilidad para sistemas de alto riesgo es real (EU AI Act, Art. 12). Sin embargo, el reglamento no prescribe cadenas hash, SHA3-256 ni anclajes a blockchain (véase §8).
- **Lorg**: existe un repositorio público que declara un archivo de memoria encadenado con SHA-256. Su existencia debe registrarse; la evaluación de sus garantías requiere inspección técnica separada.

## 3. Frente 2 — Ledgers / logs de auditoría verificables

| Sistema | Qué es | Estado 2026 |
|:---|:---|:---|
| **immudb** | DB Go con pruebas Merkle integradas, historial tx, auditor; soporta modo embebido | Muy activo: v1.11.0 (2026-04-28) añadió audit logging estructurado y verificación PG-wire |
| **Trillian → Tessera** | Transparency store Merkle de Google; diseñado como biblioteca integrable con backend POSIX | Trillian en mantenimiento; **Tessera GA v1.0 (2025-09-22)**. [Anuncio](https://blog.transparency.dev/tessera-v1-0-is-here) |
| **CT / Sigsum** | Logs de transparencia global / con witness cosigning | Vivos y modernizándose (Sunlight, TesseraCT) |
| **Amazon QLDB** | Ledger DB gestionado (journal + Merkle) | **MUERTO**: fin de soporte 2025-07-31. [AWS](https://docs.aws.amazon.com/general/latest/gr/full_shutdown_services.html) |
| **Azure Confidential Ledger** | Servicio gestionado con auditoría verificable criptográficamente (CCF) | Producción desde 2022. El cierre de QLDB no dejó vacío el mercado de ledgers gestionados. |
| **Hyperledger Fabric** | DLT permisionado empresarial | Activo: v3.1.3 (2025-10-18), SmartBFT desde v3.0 |
| **Sigstore Rekor** | Transparency log de firmas supply-chain | Muy activo: **Rekor v2 GA (2025-10-10)** (tile-backed). [Anuncio](https://blog.sigstore.dev/) |
| **OpenTimestamps** | Timestamping Merkle-calendario en Bitcoin; estándar para anclar git | Vivo como infraestructura (calendarios actualizados 2025-02). [opentimestamps.org](https://opentimestamps.org/) |
| **Dolt** | "Git para datos" SQL con grafo de commits | Activo; se posiciona como reemplazo de QLDB |

### Implementaciones Python con SQLite y cadena hash (anteriores al 19-Jul-2026)

| Paquete | Publicación PyPI | Componentes documentados | Límites observados |
|:---|:---|:---|:---|
| **`incident-ledger`** 1.0.0 | 2026-07-17 | SQLite, SHA-256, registros de inferencias/acciones de LLMs | Distribución fuente inspeccionada sin ejecución; acredita existencia de implementación, no equivalencia de seguridad ni madurez con CORTEX. [PyPI](https://pypi.org/project/incident-ledger/1.0.0/) |
| **`sovereign-sdk-ledger`** 1.3.0 | 2026-06-29 | SQLite, cadena SHA-256, triggers, `BEGIN IMMEDIATE`, verificación contra referencia | Distribución fuente inspeccionada sin ejecución; documenta transacciones y verificación local. [PyPI](https://pypi.org/project/sovereign-sdk-ledger/) |

Estos paquetes refutan la afirmación de que no existía ninguna implementación Python + SQLite + cadena hash orientada a agentes antes del 19 de julio de 2026. No se ha evaluado la equivalencia de sus garantías, cobertura de tests ni modelo de amenazas con respecto a cortex-persist; esa comparación requiere inspección técnica dedicada.

## 4. Frente 3 — Checkpointing / persistencia de estado de agentes

| Framework | Persistencia | ¿Hash-chain de la secuencia? | Notas de seguridad |
|:---|:---|:---:|:---|
| **LangGraph checkpointers** | Snapshots inmutables por paso (Memory/Sqlite/PostgresSaver); time-travel | No | **CVE-2025-64439** (RCE por deserialización en `langgraph-checkpoint` < 3.0.0) y **CVE-2025-67644** (SQLi en `langgraph-checkpoint-sqlite` < 3.0.1, CVSS 7.3). Corregidos en sus versiones respectivas. [Advisory](https://github.com/langchain-ai/langgraph/security/advisories/GHSA-wwqv-p2pp-99h5) |
| **Temporal** | Event history durable + replay determinista | No (durable y rejugable, no hash-encadenado; confianza = operador del cluster) | — |
| **AutoGen / MS Agent Framework** | `[OBSOLETO: save_state]`/`[OBSOLETO: load_state]` JSON; la guía oficial dice que la persistencia "debe implementarse externamente" | No | — |
| **OpenAI Agents SDK** | `[OBSOLETO: SQLiteSession]`/`[OBSOLETO: SQLAlchemySession]`/EncryptedSession | Sin hash-chain de la secuencia | EncryptedSession utiliza Fernet (AES-128-CBC + HMAC-SHA256): cifrado autenticado que protege integridad y confidencialidad de cada mensaje frente a actores sin la clave. Eso no equivale a verificabilidad del historial (completitud, orden, ausencia de eliminaciones). [Docs](https://openai.github.io/openai-agents-python/sessions/encrypted_session/) |

**Separación de propiedades:** los CVEs citados demuestran que las capas de persistencia también necesitan revisión de seguridad. De esos fallos **no se deduce** que todos los frameworks carezcan necesariamente de integridad criptográfica en general, ni que incorporar una cadena hash evite por sí sola una RCE o una SQLi. Un sistema puede encadenar perfectamente los bytes de un objeto malicioso y después deserializarlo de forma insegura. Son propiedades ortogonales.

**Distinción necesaria en EncryptedSession:** cifrado en reposo e integridad del historial son propiedades diferentes, pero Fernet sí aporta integridad criptográfica del contenido individual de cada mensaje. "Sin hash-chain" y "sin integridad criptográfica" no son sinónimos.

## 5. Frente 4 — BFT ligero para auditoría

- Linaje verificado: **HotStuff** (Yin et al., 2019) → LibraBFT → DiemBFT v4 → **Jolteon** ([arXiv:2106.10362](https://arxiv.org/abs/2106.10362)); AptosBFT = rebrand de DiemBFT v4; Flow usa Jolteon en producción; Fabric v3.0 integra SmartBFT.
- Suelo PBFT: tolerar *f* bizantinos exige **3f+1 réplicas** (mínimo real: 4 nodos). Esta formulación corresponde a modelos parcialmente síncronos (HotStuff, [arXiv:1803.05069](https://arxiv.org/abs/1803.05069)); no debe presentarse como ley universal independiente de los supuestos del protocolo.
- **"BFT consigo mismo" (N=1) NO es un patrón establecido**: con una réplica el consenso es vacuo. El patrón ortodoxo para integridad en un nodo es **cadena hash tamper-evident + anclaje en transparency log / witness cosigning** (immudb, CT, Sigsum, OTS) — el diseño declarado de cortex-persist.
- **Sobre la etiqueta "swarm-ready":** debe sustituirse por una descripción comprobable del estado de la implementación. No se han acreditado aquí pruebas con réplicas, cambios de líder ni comportamiento bizantino. El single-writer actor es la frontera de integridad correcta y ortodoxa a N=1.

## 6. Propiedades de cortex-persist y sus límites

Conforme al [modelo de seguridad](../../01_spec/spec_security_model.md) revisado el 2026-10-26:

| Mecanismo | Propiedad que puede aportar | Condición o límite |
|:---|:---|:---|
| Cadena hash (SHA3-256) | Detección de alteraciones respecto a un compromiso de referencia. | Si el atacante puede reemplazar datos y referencias locales, puede reconstruir una cadena coherente. Requiere checkpoint externo de confianza. |
| Escritor único (single-writer) | Serialización y simplificación del orden de escritura. | No autentica al escritor ni impide que omita un evento antes de su inserción. |
| UUIDv5 | Identidad determinista para una entrada definida por sus campos. | La idempotencia depende de la clave y la transacción. No garantiza ejecución exactamente una vez de efectos externos. |
| Reloj de Lamport | Orden lógico compatible con relaciones causales bajo su protocolo. | *a* → *b* ⟹ *L*(*a*) < *L*(*b*). La implicación inversa no está garantizada: una secuencia creciente no basta para afirmar reconstrucción causal completa. [Lamport, 1978](https://lamport.azurewebsites.net/pubs/time-clocks.pdf) |
| Anclaje OTS | Evidencia temporal: determinados datos existían antes de un bloque de Bitcoin. | Debe verificarse el anclaje concreto (raíz/checkpoint, recibo, alcance de eventos cubiertos, resultado de verificación). No prueba ejecución, completitud del log ni veracidad del contenido. [opentimestamps.org](https://opentimestamps.org/) |

**OTS del código y OTS del historial operativo son evidencias diferentes:**
- Anclar un commit aporta evidencia temporal sobre el contenido comprometido.
- Anclar una raíz del ledger puede aportar evidencia temporal sobre ese historial.
- Ninguna de esas operaciones prueba por sí sola que el programa se ejecutó, que registró todos los efectos o que lo registrado era verdadero.

La convivencia de perfiles criptográficos (BLAKE3 canónico, SHA-256 en testigos, SHA3-256 en sobres Python) no es por sí misma un defecto; la discrepancia aparece cuando se describe toda la plataforma como si tuviera un único perfil o se atribuyen a formatos históricos garantías de otro componente. Véase [perfil criptográfico](../../01_spec/spec_cryptographic_profile.md).

## 7. Marco académico (Scholar, jul 2026)

| Paper | Venue / Año | Relevancia |
|:---|:---|:---|
| MemoryOS of AI Agent (Kang et al.) | EMNLP 2025 | SOTA de memoria jerárquica; baseline de recuperación |
| LD-Agent (Li et al.) | NAACL 2025 | Memoria de diálogo a largo plazo personalizada |
| Reflective Memory Management (Tan et al.) | ACL 2025 | Gestión prospectiva/retrospectiva de memoria |
| Toward Personalized LLM-powered Agents (Xu et al.) | Survey 2026 | Marco de 4 capacidades; foco en memoria externa |
| **LedgerDB** (Yang et al., Alibaba) | **VLDB 2020** | Referente académico de ledger DB centralizado tamper-evident |
| Trust, but Verify: Audit-ready logging for clinical AI (Joseph) | 2023 | Demanda de logging audit-ready para IA regulada |
| Blockchain-Based Access Logs / LogProof | 2025 | Frameworks de audit trails tamper-proof (tendencia) |

*Los conteos de citas de Scholar incluidos en la v1.0.0 se han eliminado: son volátiles, no se conservaron consultas ni exportaciones reproducibles, y no pueden acreditarse como históricos.*

## 8. Marco regulatorio (actualización AI Omnibus)

El artículo 12 del [Reglamento (UE) 2024/1689](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02024R1689-20260727) exige capacidades de registro automático y trazabilidad para sistemas de IA de alto riesgo. No prescribe cadenas hash, SHA3-256, blockchain ni anclajes a Bitcoin. La verificabilidad criptográfica puede contribuir a la evidencia de cumplimiento; no equivale por sí sola a satisfacer el reglamento.

El [AI Omnibus](https://digital-strategy.ec.europa.eu/en/news/ai-omnibus-enters-force), en vigor desde el 27 de julio de 2026, modificó el calendario de aplicación de los requisitos para sistemas de alto riesgo:

| Categoría | Fecha revisada de aplicación |
|:---|:---|
| Sistemas del artículo 6.2 / anexo III | 2 de diciembre de 2027 |
| Sistemas del artículo 6.1 / anexo I | 2 de agosto de 2028 |

El documento original estaba fechado ocho días antes de la entrada en vigor de esa reforma. Se conserva su fecha histórica; el calendario del v1.0.0 no debe utilizarse como argumento comercial vigente.

## 9. Análisis comparativo

En lugar de afirmar una "intersección vacía" por acumulación de requisitos ad-hoc, la comparación defendible debe contestar preguntas operativas:

1. ¿Qué manipulaciones detecta cada sistema?
2. ¿Contra qué atacante y con qué referencia de confianza?
3. ¿Qué necesita desplegar el usuario?
4. ¿Puede un tercero verificar la evidencia?
5. ¿Cuánto cuesta integrar, mantener y verificar esa solución?

### Posicionamiento defendible

El valor de cortex-persist puede formularse así:

> CORTEX-Persist integra persistencia local para agentes, procedencia de eventos, verificación criptográfica y anclaje externo en una experiencia de uso Python. Existen bibliotecas y servicios que cubren partes relevantes de esta combinación, incluidos paquetes SQLite con cadenas hash publicados antes de julio de 2026. Su diferenciación debe evaluarse mediante las garantías ofrecidas, la facilidad de integración y la evidencia que un tercero puede verificar.

La selección exacta de componentes, por sí sola, no acredita la ventaja. La ventaja que merece demostrarse es cuánto trabajo ahorra CORTEX para producir y verificar evidencia fiable dentro de un perímetro concreto. Esa afirmación puede sobrevivir a la aparición de competidores.

### Coherencia con las especificaciones internas

| Documento | Criterio que ya contiene | Consecuencia para este SOTA |
|:---|:---|:---|
| [Modelo de seguridad](../../01_spec/spec_security_model.md) (2026-10-26) | Retira el sello genérico "Verified"; distingue mecanismo observado de garantía acreditada. | El badge genérico se ha retirado de esta revisión. |
| [Perfil criptográfico](../../01_spec/spec_cryptographic_profile.md) | Separa BLAKE3, SHA-256 y SHA3-256 según superficie y formato. | "SHA3-256 por evento" se refiere al ledger Python y su `compute_envelope_hash`. |
| [README de la proyección pública](../../README.md) | Declara el kernel como alpha de seguridad; condiciona la protección a broker y confinamiento del SO. | La trazabilidad de memoria no debe presentarse como prueba de mediación obligatoria de efectos. |

## 10. Veredicto y riesgos

1. **Posicionamiento defendible:** *"persistencia local para agentes con verificación criptográfica del historial bajo un modelo de amenazas documentado"*. La comparación debe hacerse por garantías concretas, no por ausencia total de competidores.
2. **Demanda regulatoria real pero con plazos actualizados:** los requisitos de alto riesgo del AI Act se aplican a partir de diciembre de 2027 (Art. 6.2) y agosto de 2028 (Art. 6.1). La trazabilidad criptográfica contribuye; no equivale a cumplimiento.
3. **Riesgo de convergencia:** es previsible que otros frameworks añadan "integrity features" (la presión de compliance es pública). La defensa sostenible es la calidad del modelo de amenazas, la verificabilidad independiente y el coste de integración.
4. **Riesgo narrativo:** no vender BFT a N=1 (§5). No afirmar exclusividades universales que encuentran contraejemplos en repositorios públicos. Vender "single-writer ortodoxo + tamper-evidence + anclaje externo + modelo de amenazas acotado".

## 11. No verificado (no citar como hecho)

- Fecha exacta de immudb v1.11.1 (posterior a v1.11.0, 2026-04-28).
- Estado de mantenimiento actual del repo Generative Agents.
- Detalles del paper original MemoryBank 2023 (Zhong et al.) — conocimiento de fondo, no re-verificado.
- Fallo judicial EU sobre valor probatorio de OTS (TJ Marseille 2025-03-20) — fuente: un vendor, sin confirmación independiente.
- LongMemEval 93.4% de Mem0 (abr 2026) es cifra auto-reportada por Mem0.
- Estado actual de monetización de TrustWarden (términos públicos describen prelanzamiento; pueden estar desactualizados).
- Estado de EncryptedSession en el SDK de OpenAI: la v1.0.0 la marcaba como `[OBSOLETO]`; debe verificarse contra la documentación vigente del proyecto.

---

*Fuentes web: docs oficiales y GitHub de cada proyecto, transparency.dev, blog.sigstore.dev, opentimestamps.org, PyPI (distribuciones fuente de incident-ledger y sovereign-sdk-ledger), InfoQ, CSA Labs, advisories de seguridad, EUR-Lex (texto consolidado del Reglamento 2024/1689), Comisión Europea (AI Omnibus) — recopiladas el 2026-07-19 (v1.0.0) y actualizadas el 2026-11-07 (v2.0.0). Fuentes académicas vía Scholar (§7). Las referencias se vinculan en cada afirmación; una lista de dominios sin versión no sustituye a la citación específica.*

*Este documento es un análisis de posicionamiento. No acredita una nueva capacidad del runtime ni constituye una evaluación de cumplimiento regulatorio. La revisión v2.0.0 incorpora la auditoría epistémica del 2026-11-07.*
