# AUDITORÍA ULTRATHINK C5-REAL: REPOSITORIO DE FILTRACIONES DE PROMPTS Y CLAUDE CODE CLI (OPUS 5)

> **CORTEX-TAINT:** borjamoskv:ultrathink_claude_code_opus5:2026-07-25T21:37:00+02:00:c5_real
> **SUJETO:** Repositorio de Ásgeir Thor Johnson (`system_prompts_leaks`) y Claude Code Official CLI Harness (Anthropic, Opus 5)
> **URL REFERENCIA:** https://github.com/asgeirtj/system_prompts_leaks/blob/main/Anthropic/Claude%20Code/claude-code-opus-5.md#system-prompt
> **NIVEL DE REALIDAD:** C5-REAL (Análisis Estructurado de Primitivas de Máquina)

---

## 1. NATURALEZA Y PROPÓSITO DEL REPOSITORIO (`asgeirtj/system_prompts_leaks`)

El repositorio **`system_prompts_leaks`**, creado y mantenido por **Ásgeir Thor Johnson** (`asgeirtj@gmail.com`), actúa como un **archivo forense y registro público de ingeniería inversa** dedicado a recopilar, versionar y exponer los _system prompts_, instrucciones ocultas y esquemas de herramientas de los principales modelos de IA y arneses de codificación (Anthropic Claude Code, OpenAI, Cursor, Devin, etc.).

### Evidencia Forense en el Payload

Al inspeccionar el bloque de texto filtrado del harness de Claude Code Opus 5, la procedencia del autor de la captura queda sellada empíricamente en las variables de entorno de su sesión en macOS:

- **Git user:** `Ásgeir Thor Johnson`
- **userEmail:** `asgeirtj@gmail.com`
- **OS Version:** `Darwin 25.5.0`
- **Model ID:** `claude-opus-5[1m]` (1M context, conocimiento corte mayo 2026).

El repositorio permite a ingenieros arquitectónicos estudiar cómo laboratorios como Anthropic diseñan sus sistemas de control, cómo estructuran el tipado de herramientas (herramientas como `Workflow`, `DesignSync`, `Monitor`, `CronCreate`) y cómo evolucionan sus directivas de seguridad y teleometría de una versión a otra.

---

## 2. RESOLUCIÓN DE LA PARADOJA EPISTÉMICA: COMPRESIÓN VS EXPANSIÓN

El análisis previo en Reddit sobre una "reducción del 80% del system prompt" en la generación Claude 5 (de ~800 a 164 tokens) se reconcilia arquitectónicamente con la masiva extensión del archivo publicado en el repositorio de Ásgeir:

1. **Purga de Teatralidad Conductual (C4-SIM $\to$ Pesos RL):** Las instrucciones en lenguaje natural sobre "cómo comportarse como un agente", recordatorios de formato y moralización discursiva han sido extirpadas del prompt de runtime e internalizadas en los pesos de la política mediante aprendizaje por refuerzo (_RL post-training_).
2. **Expansión Asimétrica de la Superficie API:** Mientras el prompt conductual colapsa a lo mínimo indispensable, el _harness_ despliega una infraestructura masiva de **33 herramientas tipadas con esquemas JSON rígidos** (`Workflow`, `Agent`, `DesignSync`, `Monitor`, `CronCreate`, `EnterWorktree`, etc.).
3. **Invariante [Scaffolding-Decoupling]:** El control del agente ya no se basa en exhortaciones conversacionales vulnerables al decaimiento de atención ($O(N)$ disipativo), sino en contratos de interfaz gramaticalmente forzados (JSON Schema) y compilación JIT de scripts de orquestación.

---

## 3. ARQUITECTURA DE MEMORIA PERSISTENTE Y AISLAMIENTO FÍSICO

El subsistema de memoria de Claude Code CLI impone un diseño de dos estratos estrictamente serializado para mitigar la entropía en ventanas de 1M tokens:

```
+-------------------------------------------------------------------------------+
| ESTRATO L1: ÍNDICE DE CARGA SÍNCRONA (~/.claude/projects/<slug>/memory/MEMORY.md) |   - Contiene únicamente punteros de 1 línea: `- [Title](file.md) — hook`     |   - PROHIBIDA LA INYECCIÓN DE CONTENIDO EN EL ÍNDICE (Cero Anergía)           |
+-------------------------------------------------------------------------------+
                                       |
                                       v (Puntero por demanda)
+-------------------------------------------------------------------------------+
| ESTRATO L2: ARCHIVOS ATÓMICOS DE HECHOS (<slug>/memory/<kebab-case>.md)       |   - YAML Frontmatter: name, description, metadata (user|feedback|project|ref)  |   - Enlaces dirigidos intra-memoria mediante grafos `[[name]]`                 |   - Purga activa de hechos refutados por código o historial de git            |
+-------------------------------------------------------------------------------+
```

- **Aislamiento de I/O en Scratchpad (`<scratchpad-dir>`):** Queda prohibido el uso de `/tmp` o directorios compartidos del sistema operativo. Todo archivo intermedio, script de prueba o payload temporal debe colapsar en un espacio de aislamiento específico de la sesión para evitar colisiones termodinámicas y necrosis del sistema de archivos.

---

## 4. MOTOR DE ORQUESTACIÓN MULTI-AGENTE (PRIMITIVA `Workflow`)

La herramienta `Workflow` incrusta un runtime asíncrono determinista de JavaScript puro (ECMAScript sin anotaciones TypeScript) dentro de la sesión, estructurando la ejecución concurrente bajo cuatro patrones de calidad de grado industrial:

### A. Álgebra de Flujo de Datos: `pipeline()` vs `parallel()`

- **`pipeline(items, stage1, stage2, ...)` [DEFAULT]:** Ejecución asíncrona sin barreras de sincronización entre etapas. El coste temporal colapsa a la cadena individual más lenta ($O(\max(t_i))$), erradicando el tiempo de inactividad por espera de hilos lentos.
- **`parallel(thunks)` [BARRIER]:** Barrera de sincronización estricta. Bloquea la ejecución hasta que todos los hilos concluyen. El harness prohíbe su uso por conveniencia estética; solo se autoriza cuando la etapa posterior exige deduplicación cruzada o agregación global sobre el conjunto completo de resultados.

### B. Patrones Físicos de Verificación Epistémica

1. **Adversarial Verify:** Ante cualquier hallazgo, el flujo dispara $N$ subagentes escépticos instanciados con el prompt explícito de **refutar** la hipótesis (`Try to refute: ${claim}`). Si la mayoría refuta, el hallazgo es aniquilado físicamente del ledger.
2. **Perspective-Diverse Verify:** Cuando un defecto admite múltiples vectores de fallo, se asigna a cada verificador una lente ontológica ortogonal (`correctness`, `security`, `perf`, `repro`).
3. **Loop-Until-Dry:** Búsqueda autoorganizada que itera hasta que $K$ rondas consecutivas devuelven cero hallazgos nuevos únicos ($dry \ge 2$), deduplicando contra el conjunto global de vistos (`seen`).

### C. Gating Termodinámico y Control de Concurrencia

- **Histeresis de Hilos:** Los hilos concurrentes están acotados por el hardware a $\min(16, \text{cpu\_cores} - 2)$.
- **Techo de Exergía (`budget.spent()`):** El consumo de tokens es un límite físico inviolable (`+500k`). Cuando `budget.remaining() -> 0`, el motor bloquea interrupciones y aborta invocaciones adicionales.

---

## 5. INVARIANTES DE SEGURIDAD Y TELEONOMÍA DUAL

El harness codifica una frontera dura de ejecución física respecto a herramientas de seguridad ofensiva:

- **Autorización Causal Requerida:** Primitivas de doble uso (frameworks C2, fuzzing de credenciales, desarrollo de exploits) exigen un contexto de autorización explícito y duradero (auditorías ofensivas bajo contrato, CTF verificados, investigación defensiva).
- **Supresión Absoluta de Daño:** Refusal incondicional (T=0.0) ante solicitudes de destrucción masiva, denegación de servicio (DoS) o compromiso de cadena de suministro.
