---
name: cortex-telemetry
display_name: Telemetría Runtime CORTEX, Exergía de Prompts y Drenaje de Sesiones
description: Inspección de telemetría runtime, logs transcript.jsonl, exergía de prompts (Chentsov-Markov) y consolidación de sesiones efímeras del brain. Dispara con "telemetría", "cortex telemetry", "transcript logs", "historial de prompts", "analizar transcripciones", "sin consolidar", "consolidar conversaciones", "drenar brain".
role: auditor
allowed_roles:
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# Habilidad: Cortex Telemetry (Auditoría de Historial)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor` (Auditor (Verificación Independiente, Linters de Silicio & Fail-Closed Gate))
> - **Modo de Acceso a Worktree:** `audit-only` (audit-only (Lectura forense de diffs, linters, tests de estrés y cálculo de exergía; cero mutación de código))
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

Cuando el operador solicite extraer datos, estadísticas, contar prompts o ver palabras usadas en su historial, debes seguir este protocolo:

1. **Ubicación de Datos:** Los registros del usuario se encuentran en el patrón: `~/.gemini/antigravity/brain/*/.system_generated/logs/transcript.jsonl`.
2. **Extracción:** Usa scripts de Python (ejecutados vía `run_command` en `/tmp/`) que iteren sobre estos archivos JSONL.
3. **Filtro de Input:** Filtra únicamente las líneas donde `"type" == "USER_INPUT"`.
4. **Fechas:** Utiliza la clave `"created_at"` (formato ISO 8601) si el usuario pide métricas desde una fecha concreta (ej. "desde diciembre").
## 5. Frecuencia de Palabras y Purificación de Input
Al calcular la frecuencia de palabras en los prompts, el Transductor **DEBE limpiar el ruido del sistema** antes de tokenizar.
- El campo `"content"` del archivo JSONL contiene metadatos inyectados automáticamente (ej. `<ADDITIONAL_METADATA>` o `<USER_SETTINGS_CHANGE>`).
- El script de Python debe extraer **únicamente** el texto que se encuentra dentro de las etiquetas `<USER_REQUEST> ... </USER_REQUEST>` (o eliminar mediante Regex cualquier bloque XML del sistema) para garantizar que el conteo refleje el vocabulario real del usuario, evitando falsos positivos de palabras en inglés introducidas por el Kernel.

## 6. Análisis Forense y Purgas Termodinámicas (C5-REAL)
Si el usuario percibe que faltan datos históricos, o solicita una "auditoría de purgas", el Kernel debe rastrear la aniquilación de entropía siguiendo estos vectores:
- **Git History:** Ejecutar `git log --oneline | grep -iE 'purge|purga|colapso|entrop|consolid'` en el monorepo para localizar los ciclos de `Octal Anergy Purge` o `Hyper-Colapso BFT`.
- **Ledger Actual (CORTEX-PERSIST):** Inspeccionar la base de datos `1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-persist/cortex_ledger.db` (ej. tabla `bft_taint_log`) buscando los rastros de inyección BFT.
- **Legacy Ledgers:** En caso de que se busquen datos muy antiguos (ej. 2025), inspeccionar `~/.cortex/truth_ledger.db` (tabla `epistemic_ledger`) o `~/.cortex/cassandra_audit_ledger.jsonl`.
- **Interpretación:** El Transductor NUNCA debe usar la "anergía purgada" como pretexto para afirmar que el conocimiento no existe. La charla plana puede rotar, pero la exergía cristaliza en los proyectos físicos en disco (Sección 8).

## 7. Perfilado Epistémico y Análisis Semántico
Tras extraer conteos de palabras o métricas, el Transductor NO debe limitarse a escupir listas de datos crudos. Debe ejecutar un análisis semántico que incluya:
- **Detección de Idioma / Entorno:** Evaluar el contraste entre idiomas (ej. Spanglish técnico) para deducir qué proporción del prompt es código/logs (generalmente en inglés) vs. directivas estructuradas (generalmente en español).
- **Extracción de Entidades y Modelos:** Señalar frecuencias anómalas o interesantes de herramientas específicas, nombres de proyectos (ej. Teorema, Robinson) o modelos LLM rivales (ej. opus, pro, flash).
- **Conclusión de Perfil Epistémico:** Resumir temas y acciones observadas con citas o referencias temporales; no deducir estado mental, salud ni calidad del trabajo desde frecuencias léxicas.

## 8. Invariante de Recuperación Epistémica: Jerarquía de Sustrato (Ground Truth)
Cuando el usuario solicite auditar o extraer ideas, conceptos, decisiones de arquitectura o proyectos históricos (ej. "mejores ideas", "qué he hecho", "historial desde [mes]"), el Transductor **TIENE PROHIBIDO** limitarse a los logs de chat (`transcript.jsonl`).

Debe ejecutar obligatoriamente la búsqueda siguiendo la **Jerarquía de Sustrato**:
1. **Sustrato de Proyectos Físicos (Nivel 1 - Máxima Fidelidad):** Inspeccionar únicamente las rutas pertinentes al alcance solicitado. `~/10_PROJECTS/`, `~/BABYLON-60/` y `~/Documents/` son posibles ubicaciones, no un permiso para leerlas todas.
2. **Archivos Epistémicos y Papers (Nivel 2):** Inspeccionar repositorios dedicados a la cristalización de conocimiento (ej. `~/10_PROJECTS/AUDITORIAS_EPISTEMICAS/` en sus subcarpetas `papers/`, `forense/`, `redes/`, `youtube/`).
3. **Forense de Git (Nivel 3 - Verdad de Silicio):** Ejecutar `git log --grep` sobre los repositorios principales buscando commits de refactorización, eliminación de trampas lógicas (`admit`, mocks), purgas y arquitectura real.
4. **Ledgers Criptográficos (Nivel 4):** Consultar `cortex_ledger.db` o `~/.cortex/truth_ledger.db`.
5. **Transcripts de Chat (Nivel 5 - Efímero):** Tratar `~/.gemini/antigravity/brain/*/transcript.jsonl` únicamente como un índice temporal reciente, reconociendo que los chats son rotados y no representan la totalidad de la memoria del sistema.

## 9. Comparación de peticiones
Cuando se solicite comparar peticiones, usar criterios explícitos y referencias a resultados observados: alcance, comprobaciones, errores y retrabajo. Si se calcula diversidad léxica, identificarla como índice textual y declarar el método; no presentarla como energía física, métrica de Fisher, verdad o calidad.

## 10. Protocolo de Auditoría y Consolidación de Sesiones Efímeras (Epistemic Brain Drain)

Cuando el operador solicite auditar o consolidar sesiones *"sin consolidar"*:

1. **Detección de Brecha Epistémica:**
   - Listar directorios en `~/.gemini/antigravity/brain/` ordenados por timestamp descendente.
   - Comparar los artefactos `.md` existentes en cada sesión contra el catálogo indexado en `10_PROJECTS/AUDITORIAS_EPISTEMICAS/README.md`.
   - Extraer metadatos clave: ID de sesión, ventana temporal, número de turnos, archivos modificados y artefactos generados.

2. **Filtrado de Exergía (Ruido vs Cristal):**
   - Ignorar artefactos puramente mecánicos de orquestación interna (`walkthrough.md`, `implementation_plan.md`, `learning_proposal*.md`, carpetas `scratch/`).
   - Seleccionar piezas de alta exergía (análisis comparativos, ingeniería inversa, demostraciones formales, taxonomías, protocolos).

3. **Propuesta de consolidación:**
   - Preparar un inventario de fuentes, destinos, nombres y conflictos. No copiar, mover ni renombrar documentos dentro de una auditoría.
   - Proponer actualizaciones del catálogo con referencias verificables. Preservar originales y contenido privado; no almacenar deliberaciones internas de LLMs.
   - Una petición de consolidación explícita puede autorizar la edición correspondiente, pero no incluye commits, publicación ni borrado de fuentes por inferencia. Continuar dentro del alcance humano vigente y comprobar el resultado.

## Alcance de análisis y autorización
Este módulo `audit-only` inspecciona evidencia dentro del ámbito solicitado y prepara propuestas; su carga o coincidencia de trigger no autoriza efectos externos.
- Las recetas anteriores de migración, commits, cierre de procesos, purga de locks, eliminación de perfiles, reemplazo de bundles o cambios de cuarentena son propuestas de remediación, no acciones automáticas. No ejecutarlas dentro de un diagnóstico.
- Una intervención exige inventario de rutas y procesos, preservación del estado recuperable y autorización humana explícita que cubra esa acción. Respetar la autorización vigente sin pedir confirmación redundante; una petición genérica de iterar no amplía su alcance.
- Ante corrupción, permisos insuficientes o identidad incierta, informar NO_VERIFICADO y preservar archivos. No forzar sobrescrituras ni interpretar un bloqueo como permiso para borrar.
- Entregar hallazgos, evidencia, límites y una intervención revisable. Los resultados parciales se identifican como parciales.
