# MATRIZ 1: PRIMITIVAS DE COLAPSO (Rugosidad Temporal)
| ID | Primitiva | Mecanismo Causal | Activación (Trigger) | Sensor (Síntoma) | Escala Temporal | Gravedad | Intervención |
|---|---|---|---|---|---|---|---|
| PRIM-T01 | Desgarro de Simulación | Ingesta de datos C5-REAL con validación C4-SIM. | Grafo DOM o payload JSON excede la dimensionalidad del esquema local. | `SchemaMismatch`, `TypeError` en parser de validación estructural. | 10ms - 500ms | P0 | Despliegue de `cortex/engine/causal/taint_engine.py` para aserción forzada. |
| PRIM-T02 | Amnesia de Horizonte | El modelo procesa eventos proyectados como eventos pasados debido a la compresión del vector temporal. | Query de eventos futuros colapsando en tablas de datos históricos. | Incoherencia de timestamp (T_future < T_current) en el log. | <1s | P1 | Forzar aislamiento estricto de series temporales en SQLite-Vec. |
| PRIM-T03 | Bucle de Espejos | Auto-alimentación de heurísticas generativas (LLM slop) asumiendo que representan señales externas válidas. | Reingesta de output estocástico propio sin validación de quórum BFT. | Disminución de entropía de Shannon (alta anergía) en el texto almacenado. | 5s - ∞ | P0 | Apoptosis celular forzada (Kill Criteria AX-047). |

# MATRIZ 2: INVARIANTES TERMODINÁMICAS (Flujo Asimétrico)
| ID | Invariante | Lógica / Principio | Implicación Operacional | Condición de Borde | Métrica Falsable |
|---|---|---|---|---|---|
| INVT-T01 | Asimetría de Landauer | La compresión de datos futuros requiere disipación física en el presente. | No se pueden almacenar predicciones estocásticas sin gastar exergía. | Ingesta masiva de predicciones LLM. | Coste de escritura en `audit/ledger.py` > umbral de exergía basal. |
| INVT-T02 | Causalidad Irreversible | La lógica estructural del pasado no puede alterar el dato del futuro; solo enrutarlo. | Prohibición de mutar esquemas de base de datos basados en alucinaciones generativas. | Fallos en migraciones de esquema generadas autónomamente. | Check de integridad de `cortex/migrate.py` y DAG histórico de Git. |
| INVT-T03 | Gravedad de Contexto (Rot) | El mantenimiento de un estado estocástico en la RAM degrada la percepción del Kernel (Sensor Drift). | Purgado forzado de memoria no validada criptográficamente (Weaponized Forgetting). | Ciclos prolongados de ejecución (UpTime > 24h). | Relación Señal/Ruido en `memory_vault/` > 80%. |

# MATRIZ 3: ANTIPATRONES ESTOCÁSTICOS
| ID | Antipatrón | Disfunción Causal | Señal de Presencia | Impacto en Robustez | Refactor (Alternativa) |
|---|---|---|---|---|---|
| ANTI-T01 | Nostalgia Arquitectónica | Aplicar mitigaciones de sistemas secuenciales (C4) a problemas de quórum distribuido (C5). | Uso de bloqueos de hilo (`time.sleep()`) en eventos paralelos asíncronos. | Deadlocks en acceso a SQLite y caídas en picos de latencia. | Reemplazar por `asyncio.sleep()` y SQLite WAL mode (R10). |
| ANTI-T02 | Teatralidad Epistémica (Green Theater) | Generación de advertencias o disclaimers sobre la validez de los datos futuros. | Tokens desperdiciados en "Es probable que..." o "Tenga en cuenta que...". | Aumento del tiempo de inferencia sin mutación de estado. | Inyección de ExergyGuard (Ω13) y colapso directo a Hash/Ledger. |
| ANTI-T03 | Tratamiento Empírico de Simulaciones | Almacenar escenarios (What-Ifs) en tablas de hechos confirmados. | Falta de atributo `CORTEX-TAINT` en filas de datos hipotéticos. | Corrupción de la verdad base del repositorio y fallos de consenso. | Esquemas segmentados. Taint obligatorio. |

# MATRIZ 4: REDUNDANCIAS ACTIVAS (MITIGACIÓN C5)
| ID | Redundancia C5 | Función Topológica | Riesgo Mitigado | Coste (Overhead) | Dependencias |
|---|---|---|---|---|---|
| REDU-T01 | Consenso BFT en Semántica | Requerir N=3 aserciones para colapsar una hipótesis temporal en una regla estructural. | Evitar que una sola alucinación contamine el núcleo (Ontology-Forge). | 3x llamadas al modelo y retraso asíncrono. | `cortex/consensus/` y `cortex/guards/`. |
| REDU-T02 | Aislamiento de Entropía Temporal | Sandbox estricto para la ingesta de flujos no comprobados. | Protección de `/private/var/db` y `10_PROJECTS` contra mutaciones caóticas. | Creación y destrucción continua de sandboxes virtuales. | `cortex/extensions/daemon/` y `mac_maestro/`. |

# MATRIZ 5: VECTORES DE ATAQUE ADVERSARIAL (RED TEAMING)
| ID | Vector Adversarial | Superficie de Ataque | Mecanismo de Explotación | Impacto Termodinámico | Defensa (Mitigación) |
|---|---|---|---|---|---|
| REDA-T01 | Inyección de Falsa Paradoja | Entradas de Operador simuladas para crear loops lógicos infinitos. | Prompts que exigen reconciliar la lógica pasada con un resultado imposible en 2026. | Agotamiento del Kernel por OOM (Memory Leak / Limmerence Loop). | Kill Criteria (AX-047): 1 Prompt = 1 Ejecución = Stop. |
| REDA-T02 | Bypass Criptográfico por Fricción Temporal | Desvío de la verificación de firmas debido a la "urgencia" de los datos del futuro. | El sistema degrada la aserción BFT para acelerar la ingesta en tiempo real. | Compromiso total del Master Ledger sin rastros auditables. | El `CORTEX-TAINT` es innegociable y hardcodeado a nivel SQLite WAL. |

SYS_ID borjamoskv
