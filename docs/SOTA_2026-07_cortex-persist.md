# Estado del Arte (SOTA) — Posicionamiento de cortex-persist

> **Fecha:** 2026-07-19 · **Alcance:** memoria/persistencia para agentes IA, ledgers de auditoría verificables, checkpointing de agentes y BFT ligero.
> **Método:** revisión web verificada (docs oficiales, GitHub, advisories) + búsqueda académica (Scholar). Todo lo no verificable queda marcado en §7 — no se afirma nada sin fuente.
> **Author:** Borja Moskv (`borjamoskv`)

---

## 1. Resumen ejecutivo

El SOTA de memoria para agentes (Mem0, Zep/Graphiti, Letta, LangMem, Cognee, A-MEM, MemoryOS) compite **íntegramente en calidad de recuperación** (retrieval) y tiene **cero integridad criptográfica**. El mundo de los ledgers verificables (immudb, Trillian/Tessera, Rekor, CT/Sigsum) tiene integridad pero **ni semántica de agente ni formato embebido en Python**. Los frameworks de checkpointing que la industria usa de facto (LangGraph, AutoGen, OpenAI Agents SDK) son **demostrablemente ni tamper-evident ni tamper-resistant** (CVEs 2025–2026 en la propia capa de checkpoints). La muerte de Amazon QLDB (fin de soporte 2025-07-31) dejó vacío el único "ledger DB" gestionado.

**La intersección que ocupa cortex-persist está vacía a fecha de hoy:** SQLite embebido de un solo escritor + cadena SHA3-256 por evento + reloj de Lamport + `causal_taint` + idempotencia UUIDv5 + anclaje OTS a Bitcoin, orientado a memoria de agentes y distribuido vía pip.

---

## 2. Frente 1 — Memoria para agentes IA (2025–2026)

| Sistema | Arquitectura | ¿Integridad criptográfica? | Mantenimiento (verificado) |
|:---|:---|:---:|:---|
| **Mem0** | Extracción LLM (ADD/UPDATE/DELETE); vector + grafo opcional (Mem0g) | ❌ Ninguna | Muy activo: `mem0ai` v2.0.8 (jun 2026), TS SDK v3.0.13 (2026-07-01) |
| **Zep / Graphiti** | KG bi-temporal (`valid_from/to`); Zep Cloud; Graphiti OSS sobre Neo4j/Kuzu | ❌ Ninguna (historia semántica sin prueba) | Activo: `graphiti-core` ≥0.28.2 (mar 2026). Zep CE **deprecado** (~abr 2025) |
| **Letta** (ex-MemGPT) | Runtime de agentes stateful; memoria por bloques tipo SO; Postgres/SQLite | ❌ Ninguna | Activo (Letta Code, jul 2026) |
| **LangMem** | SDK sobre LangGraph BaseStore; memoria semántica/episódica/procedural | ❌ Ninguna | Activo, pequeño (~1.5k★) |
| **Cognee** | Pipeline ECL → relacional+vector+grafo (SQLite+LanceDB+Kuzu) | ❌ Ninguna | Muy activo: v1.0.0 GA 2026-04-11; seed $7.5M (feb 2026) |
| **A-MEM** | Zettelkasten con enlaces LLM; "evolución" de notas pasadas | ❌ **Antagónica**: reescribe el pasado silenciosamente | NeurIPS 2025 (arXiv:2502.12110) |
| **MemoryOS** | Jerarquía OS (STM→MTM→LPM) por "calor"; ChromaDB | ❌ Ninguna | EMNLP 2025 Oral; release V1.2 (2025-07-18) |
| **Generative Agents** | Memory stream + reflexión (Stanford, UIST'23) | ❌ Ninguna | Artefacto de investigación |

**Señales de convergencia (demanda real):**
- **TrustWarden "AgentLedger"**: audit trail inmutable comercial para acciones de agentes (S3 Object Lock + KMS) — valida la tesis, pero cloud/propietario, no embebido.
- Comentaría de industria converge en audit trails hash-encadenados como **requisito de compliance 2026** (EU AI Act, aplicación 2026-08-02).
- "Lorg" (mención en awesome-list, 2026-03): archivo de memoria "hash-chained" — **no verificado**, trátese como rumor de que otros van hacia la misma idea.

## 3. Frente 2 — Ledgers / logs de auditoría verificables

| Sistema | Qué es | Estado 2026 |
|:---|:---|:---|
| **immudb** | DB Go con pruebas Merkle integradas, historial tx, auditor | Muy activo: v1.11.0 (2026-04-28) añadió audit logging estructurado y verificación PG-wire |
| **Trillian → Tessera** | Transparency store Merkle de Google | Trillian en mantenimiento; **Tessera GA v1.0 (nov 2025)** |
| **CT / Sigsum** | Logs de transparencia global / con witness cosigning | Vivos y modernizándose (Sunlight, TesseraCT) |
| **Amazon QLDB** | Ledger DB gestionado (journal + Merkle) | **MUERTO**: fin de soporte 2025-07-31; AWS recomienda migrar a PostgreSQL |
| **Hyperledger Fabric** | DLT permisionado empresarial | Activo: v3.1.3 (2025-10-18), SmartBFT desde v3.0 |
| **Sigstore Rekor** | Transparency log de firmas supply-chain | Muy activo: **Rekor v2 GA 2025-10-06** (tile-backed) |
| **OpenTimestamps** | Timestamping Merkle-calendario en Bitcoin; estándar para anclar git | Vivo como infraestructura (calendarios actualizados 2025-02) |
| **Dolt** | "Git para datos" SQL con grafo de commits | Activo; se posiciona como reemplazo de QLDB |
| **SQLite embebido + verificabilidad** | — | **HUECO CONFIRMADO**: solo ejemplos de juguete y literatura académica de ADS |

## 4. Frente 3 — Checkpointing / persistencia de estado de agentes

| Framework | Persistencia | ¿Hash-chain / verificabilidad? |
|:---|:---|:---|
| **LangGraph checkpointers** | Snapshots inmutables por paso (Memory/Sqlite/PostgresSaver); time-travel | ❌ Ninguna — peor: **CVE-2025-64439** (RCE por deserialización) y **CVE-2025-67644** (SQLi en SQLite checkpointer, CVSS 7.3): la capa de checkpoints es superficie de ataque, no garantía |
| **Temporal** | Event history durable + replay determinista | ❌ Durable y rejugable, pero no hash-encadenado; confianza = operador del cluster |
| **AutoGen / MS Agent Framework** | `save_state`/`load_state` JSON; la guía oficial dice que la persistencia "debe implementarse externamente" | ❌ Ninguna |
| **OpenAI Agents SDK** | `SQLiteSession`/`SQLAlchemySession`/`EncryptedSession` | ❌ Cifrado en reposo ≠ integridad; sin hash-chain |

## 5. Frente 4 — BFT ligero para auditoría

- Linaje verificado: **HotStuff** (Yin et al., 2019) → LibraBFT → DiemBFT v4 → **Jolteon** (arXiv:2106.10362); AptosBFT = rebrand de DiemBFT v4; Flow usa Jolteon en producción; Fabric v3.0 integra SmartBFT.
- Suelo PBFT: tolerar *f* bizantinos exige **3f+1 réplicas** (mínimo real: 4 nodos).
- **"BFT consigo mismo" (N=1) NO es un patrón establecido**: con una réplica el consenso es vacuo. El patrón ortodoxo para integridad en un nodo es **cadena hash tamper-evident + anclaje en transparency log / witness cosigning** (immudb, CT, Sigsum, OTS) — exactamente el diseño de cortex-persist.
- **Recomendación de marketing:** el extra HotStuff del repo debe presentarse como *"swarm-ready"* (válido cuando haya réplicas que se desconfían mutuamente), no como seguridad adicional a N=1. El single-writer actor es la frontera de integridad correcta y ortodoxa.

## 6. Marco académico (Scholar, jul 2026)

| Paper | Venue / Año | Citas | Relevancia |
|:---|:---|:---:|:---|
| MemoryOS of AI Agent (Kang et al.) | EMNLP 2025 | 182 | SOTA de memoria jerárquica; baseline de retrieval |
| LD-Agent (Li et al.) | NAACL 2025 | 151 | Memoria de diálogo a largo plazo personalizada |
| Reflective Memory Management (Tan et al.) | ACL 2025 | 97 | Gestión prospectiva/retrospectiva de memoria |
| Toward Personalized LLM-powered Agents (Xu et al.) | Survey 2026 | 8 | Marco de 4 capacidades; foco en memoria externa |
| **LedgerDB** (Yang et al., Alibaba) | **VLDB 2020** | 149 | Referente académico de ledger DB centralizado tamper-evident |
| Trust, but Verify: Audit-ready logging for clinical AI (Joseph) | 2023 | 36 | Demanda de logging audit-ready para IA regulada |
| Blockchain-Based Access Logs / LogProof | 2025 | 4 / 1 | Frameworks de audit trails tamper-proof (tendencia) |

*Datos de citación tal como los devolvió Scholar el 2026-07-19; son aproximados y de terceros.*

## 7. Gap analysis — la intersección vacía

| Propiedad de cortex-persist | Poseedores más cercanos | Hueco |
|:---|:---|:---|
| SQLite embebido local-first, single-file | LangGraph SqliteSaver, OpenAI SQLiteSession | Ninguno con integridad |
| Cadena SHA3-256 por evento | immudb, Dolt, TrustWarden | Todos servidor/cloud/propietarios; ninguno con semántica de agente |
| `causal_taint` (quién/cuándo/por qué) por evento | Prescrito por blogs de agent-audit; exigido en análisis de A-MEM | Ningún sistema de memoria OSS lo implementa |
| Reloj de Lamport en escrituras concurrentes | Literatura estándar de sistemas distribuidos | Ausente de todo framework de memoria/checkpoint revisado |
| Idempotencia UUIDv5 (dedup silencioso) | Patrón común en APIs | Ausente en write paths de Mem0/Zep/Letta/LangMem/Cognee |
| Anclaje OTS a Bitcoin del propio código/historia | OTS para IP; Rekor para artefactos | Ningún proyecto de memoria/ledger se auto-ancla |
| Todo lo anterior en un paquete Python pip, local-first, para memoria de agentes | — | **Conjunto vacío (jul 2026)** |

## 8. Veredicto y riesgos

1. **Posicionamiento defendible con datos:** *"la memoria de agentes que puedes verificar criptográficamente, no solo consultar"*. Ningún competidor OSS ocupa esa casilla hoy.
2. **Ventana de oportunidad regulatoria:** EU AI Act (2026-08-02) crea pull para audit trails tamper-evident de acciones de agentes; TrustWarden ya monetiza esa demanda en cloud.
3. **Riesgo de convergencia:** inminente que Mem0/Zep/Cognee añadan "integrity features" (la presión compliance es pública). La defensa es la combinación completa + el anclaje OTS del propio linaje (Git Sentinel) — difícil de bolting-on.
4. **Riesgo narrativo:** no vender BFT a N=1 (§5). Vender "single-writer ortodoxo + tamper-evidence + anclaje externo".

## 9. No verificado (no citar como hecho)

- Fecha exacta de immudb v1.11.1 (posterior a v1.11.0, 2026-04-28).
- Estado de mantenimiento actual del repo Generative Agents.
- "Lorg": única mención en awesome-list; sin repo/paper verificable.
- Detalles del paper original MemoryBank 2023 (Zhong et al.) — conocimiento de fondo, no re-verificado.
- Fallo judicial EU sobre valor probatorio de OTS (TJ Marseille 2025-03-20) — fuente: un vendor, sin confirmación independiente.
- LongMemEval 93.4% de Mem0 (abr 2026) es cifra auto-reportada por Mem0.

---

*Fuentes web: docs oficiales y GitHub de cada proyecto, transparency.dev, blog.sigstore.dev, opentimestamps.org, InfoQ, CSA Labs, advisories RAXE — recopiladas y fechadas el 2026-07-19. Fuentes académicas vía Scholar (§6).*
