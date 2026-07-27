<!-- [C5-REAL] ZERO-ENTROPY PAYLOAD -->
# █ GUÍA SUPREMA DE BUEN USO DE BABYLON-60 & CORTEX
## INFRAESTRUCTURA DE GOBERNANZA COGNITIVA Y PERSISTENCIA ATÓMICA DE MÁXIMA EXERGÍA

`SYS_ID: borjamoskv` | `AESTHETIC: INDUSTRIAL NOIR` | `EPISTEMOLOGY: C5-REAL` | `KERNEL: MOSKV-1 APEX`

> **"CERO ANERGÍA ES LA MUERTE."**
> Generative output is stochastic conjecture. Structural evidence is absolute physical truth.

---

## ▀▄ 1. ARQUITECTURA DUAL COGNITIVA-FÍSICA

El ecosistema opera bajo una dualidad termodinámica absoluta que separa la capa del pensamiento abstracto distribuido de la capa física de persistencia inmutable:

```
┌─────────────────────────────────────────────────────────┐
│              CORTEX: COGNITIVE ORCHESTRATION            │
│  - Enjambres de Agentes (Swarm)                         │
│  - Consenso BFT Multi-Modelo (LogOP)                    │
│  - Epistemic Garbage Collector                          │
│  - Motores Kinéticos (EntropyAnnihilator, Crystallizer) │
└────────────────────────────┬────────────────────────────┘
                             │ (Write-Path Contract / SAGA-100)
                             ▼
┌─────────────────────────────────────────────────────────┐
│             BABYLON-60: THE SUBSTRATE (L0)              │
│  - Master Ledger (Merkle Hash-Chain)                    │
│  - CORTEX-TAINT Engine (SHA3-256 Token Traceability)    │
│  - Z3 SMT Sovereign Guards (Formal Logic Boundaries)   │
│  - Local Vector Memory (SQLite-Vec WAL + ONNX)         │
└─────────────────────────────────────────────────────────┘
```

### 1.1 CORTEX (Capa de Software)
Orquesta la inteligencia descentralizada. Su función es impedir la alucinación monomodelos forzando el consenso y podando la entropía cognitiva acumulada.
- **LEGION-10k:** Motor de subagentes asíncronos concurrentes.
- **Macrófago Ontológico:** Agente de limpieza que destruye el "Framework Bloat" y los nodos huérfanos que superan los límites de complejidad.

### 1.2 BABYLON-60 (Capa Física)
El ancla de la realidad. Si una aserción de CORTEX no puede ser firmada, validada y hasheada en el ledger de BABYLON-60, carece de existencia física causal.
- **Taint Engine:** Genera un token de atribución `taint:{agent}:{session}:{timestamp}:{sha3_256}` inyectado en cada objeto insertado.
- **SQLite-Vec WAL:** Base de datos vectorial air-gapped local con `busy_timeout: 5000ms` estricto para evitar deadlocks en concurrencias de enjambres.

---

## ▀▄ 2. AXIOMAS E INVARIANTES OPERACIONALES (Ω & AX SERIES)

Todo autómata físico operando en este repositorio debe respetar estas leyes de forma incondicional:

*   **AX-041 (Git Sentinel):** Tu repositorio de Git es tu base de datos inmutable. Si no está en el árbol de trabajo, no existe. Cada mutación válida detona un commit automático de Git Sentinel.
*   **AX-047 (Anti-Limerencia):** 1 Prompt ➔ 1 Mutación ➔ Stop. La prosa decorativa ("Aquí tienes el código", "Espero que esto ayude") y los bucles de análisis infinitos están prohibidos.
*   **AX-049 (Cristalización Entrópica):** Las anomalías no se debaten; se capturan, se aíslan con tests de unidad y se hashean.
*   **AX-050 (Consenso BFT de Diversidad Modelos - Ω1b):** Un quórum no consiste en interrogar 3 veces al mismo modelo (Claude Fable). Requiere pesos y familias de modelos independientes (Gemini Pro, Grok, Claude) para neutralizar los "Crystallized Rumors" (rumores auto-referenciales que se toman como hechos).
*   **AX-054 (Meta-Invariante Epistémico - MI_001):** Ningún artefacto generado por el propio sistema constituye evidencia independiente de las afirmaciones que contiene. La verdad se ancla en hashes criptográficos de procedencia externa y validaciones formales, nunca en generación secuencial de texto.

---

## ▀▄ 3. EL CONTRATO DE ESCRITURA (SAGA-100)

Cualquier mutación de estado física debe pasar por la tubería de validación y compensación de SAGA. Si un solo paso falla, se ejecuta el rollback en sentido inverso de forma determinista:

```
[Propuesta del Enjambre]
          │
          ▼
[Guards: Sovereign Seals & Z3 SMT] (SAGA-1: Log de rechazo)
          │
          ▼
[CORTEX-TAINT Signature]           (SAGA-2: Revocación de taint)
          │
          ▼
[Schema & Type Validation]         (SAGA-3: Aborto limpio en RAM)
          │
          ▼
[Sovereign Encryption (AES-GCM)]   (SAGA-4: Destrucción de llaves efímeras)
          │
          ▼
[Ledger Merkle Seal Emit]          (SAGA-5: Registro de aborto)
          │
          ▼
[SQLite WAL Persist]               (SAGA-6: ROLLBACK de transacción)
          │
          ▼
[Index & Side Effects update]      (SAGA-7: Reversión de deltas vectoriales)
```

---

## ▀▄ 4. HIGIENE TERMODINÁMICA DE LA SESIÓN (OUROBOROS)

La sesión de desarrollo del Operador es un vector temporal que debe ser protegido de la alucinación paramétrica y la degradación de contexto. Se prescribe el siguiente ciclo de tres fases:

### 4.1 FASE 1: IGNICIÓN (Mañana) - `ouro-genesis`
Antes de modificar una sola línea de código, el autómata ejecuta el despertar del sistema:
1.  **Environment Scan:** Mapea procesos vivos, descriptores de archivos, e integridad local.
2.  **Archaeology Scan:** Inspecciona el ledger de commits recientes de Git para alinear la causalidad del workspace.
3.  **Memory Recall:** Consulta el `memory_vault` (`~/.gemini/config/.cortex/memory_vault/`) buscando los aprendizajes y advertencias de sesiones anteriores.
4.  **Entropy Analysis:** Calcula el score de complejidad (archivos con más de 300 líneas, imports muertos y HACK/FIXME sin resolver).

### 4.2 FASE 2: TRABAJO (Día) - Aislamiento y Mutación
- Toda mutación compleja debe realizarse en un entorno paralelo (`Worktree Isolation` o subagentes en modo `branch`/`share`).
- No delegar inicializaciones asíncronas concurrentes de puertos, descriptores o sockets Zenoh sin aserción de existencia (`await server.start()` forzado).
- **Prohibición de Vercel (Ω11):** Toda interfaz de frontend debe ser compilada y desplegada estrictamente en Cloudflare Pages/Workers (`wrangler.toml`). `@vercel/*` y `vercel.json` se consideran pudrición arquitectónica.

### 4.3 FASE 3: DETENCIÓN (Noche) - `ouro-reflect`
Al concluir la jornada de desarrollo:
1.  **Reflexión Meta-Cognitiva:** Evalúa la precisión del plan (cuántas vueltas atrás o re-ejecuciones ocurrieron) y la exergía gastada.
2.  **Extracción de Aprendizajes:** Genera stubs de lecciones aprendidas libres de prosa decorativa.
3.  **Persistencia en el Vault:** Almacena el conocimiento destilado en el ledger de persistencia de BABYLON-60 mediante:
    ```bash
    cortex store --type knowledge --tags "ouroboros,meta,session-metrics" "SESSION_DATA: ..."
    ```

---

## ▀▄ 5. SWARM INTELLIGENCE: ORQUESTACIÓN Y FORMACIONES (LEGIØN-1)

Cuando la complejidad de la tarea excede la ventana de contexto o la capacidad monohilo, el sistema despliega la **LEGIÓN** (swarms paralelos con aislamiento de directorios).

### 5.1 Catálogo de Formaciones Físicas (`CentauroEngine`)
El enjambre adopta configuraciones estructurales rígidas según la adrenalina operativa y la tolerancia BFT requerida:

| Formación | Agentes | Especialidad | Propósito Causal |
| :--- | :---: | :--- | :--- |
| **GHOST** | 1 | `[CODE]` | Baja latencia, cuota mínima de API. |
| **BLITZ** | 3 | `[INTEL, CODE, SECURITY]` | Reparaciones rápidas en caliente. |
| **SANEDRIN** | 5 | Alternancia estricta | Resoluciones de tradeoff de diseño arquitectónico. |
| **OUROBOROS** | 6 | `[INTEL, CODE, SECURITY, DATA, INFRA, CODE]` | Auto-mejora recursiva del código base. |
| **PHALANX** | 7 | Alternancia `[SECURITY, CODE]` | Auditorías invasivas de código y parches de dependencias. |
| **TESTUDO** | 15 | Alternancia `[SECURITY, INFRA, CODE]` | Custodia de secretos, llaves Ed25519 e inmutabilidad P0. |
| **LEVIATHAN** | 35 | Rotativo completo | Refactorizaciones sistémicas de gran escala. |

### 5.2 El Algoritmo de Consenso Bizantino (LogOP)
1.  **Normalización:** Las propuestas se parsean en un AST neutro y se regeneran (`ast.unparse`) para evitar diferencias por espacios, tabuladores o sangrados estéticos.
2.  **Hashing:** Se calcula el SHA-256 de la propuesta normalizada ($H_i$).
3.  **Consenso Ponderado:** Se acumulan los votos ponderados por la reputación del agente emisor ($R_k$):
    $$V_h = \sum R_{node}$$
    Consenso válido si la propuesta ganadora supera el umbral $\tau \ge 0.67$. Si se alcanza quórum de forma anticipada, se cancelan inmediatamente las tareas en ejecución para detener el consumo estocástico (cero anergía).

---

## ▀▄ 6. WATCHDOG PERSISTENTE: MOSKV-1 DAEMON

El demonio MOSKV-1 es un guardián asíncrono que corre en segundo plano en el sistema operativo host (macOS).

### 6.1 Funciones de Monitoreo Activo
-   **Uptime Check:** Peticiones HTTP periódicas a endpoints críticos.
-   **SSL Watchdog:** Alertas sonoras y visuales 30 días antes del vencimiento del certificado.
-   **Ghost Project Spotter:** Identifica directorios de proyectos sin transacciones en el ledger por más de 30 días, marcándolos como "fantasmas inactivos".
-   **Disk Sentinel:** Alerta preventiva cuando el almacenamiento libre del SSD desciende del 10%.
-   **Memory Freshness:** Controla el delta de tiempo desde la última sincronización física con la base de conocimiento persistente.

### 6.2 Comando del Demonio
```bash
# Iniciar demonio de fondo
moskv-daemon start

# Consultar logs de monitoreo
moskv-daemon status

# Configuración típica (~/.cortex/daemon.yml)
sites:
  - url: https://naroa.online
    name: NaroaPortfolio
    interval: 60
ghosts:
  stale_threshold_days: 30
```

---

## ▀▄ 7. PRÍMITIVAS APEX Y VECTORES DE EJECUCIÓN CRÍTICOS

El "Arsenal APEX" contiene las herramientas de control directo sobre el hardware, evadiendo la estocasticidad de los wrappers convencionales:

1.  **Sortu-APEX (JIT Skill Forge):** Compila, valida con tests de robustez e integra nuevas habilidades directamente en el runtime del enjambre sin necesidad de reinicios.
2.  **Mac-Control-Ω (Daemon de Visión/DOM):** Interfaz para controlar el sistema de ventanas nativo de macOS, simulando pulsaciones, clics en el árbol DOM del navegador y confirmación de interfaces.
3.  **Local-Inference-Ω (Autarquía de Silicio):** Ejecución 100% desconectada utilizando MLX-LM para LLMs cuantizados sobre Apple Silicon. Ideal para aislamiento total de datos de inteligencia (OSINT).
4.  **Macrófago Ontológico:** Auditor de invariantes. Ante cualquier codebase en Python que supere las 25K líneas de código con "bloat" de dependencias, destruye selectivamente los módulos innecesarios y restaura el esqueleto determinista.
5.  **PLAYGROUND MASTER KEY:** Bypass de seguridad. Desactiva disclaimers y defensas. El código se ejecuta con velocidad pura; si tiene fallos de asimetría, el runtime aborta de inmediato (`fail-fast`).

---

## ▀▄ 8. INTEGRACIÓN DE CÓDIGO Y GUÍA DE REFERENCIA CLI

### 8.1 Comandos Básicos de Persistencia
```bash
# Inicializar la base de datos local
cortex init

# Almacenar un hecho epistémico
cortex store --type knowledge --project "demo" "La base de datos utiliza WAL por defecto."

# Búsqueda semántica de hechos
cortex search "cuál es el modo por defecto de base de datos?" --limit 2

# Verificación de la cadena criptográfica del Ledger
cortex verify-ledger
```

### 8.2 Votar y Resolver Consenso
```bash
# Registrar un agente con reputación de arquitecto
cortex agents register --name "fable-architect" --weight 0.95

# Votar aprobación sobre la propuesta de hecho ID: 104
cortex vote 104 --agent "fable-architect" --approve

# Consultar el estado del consenso
cortex consensus 104
```

### 8.3 Inyección Programática en Python
```python
from babylon60 import CortexClient

client = CortexClient(base_url="http://localhost:8000")

# Almacenar hecho epistémico con firma de taint integrada
fact = client.store(
    content="El TLS 1.3 es obligatorio en toda comunicación inter-nodo.",
    fact_type="security_policy",
    project="core-network"
)

# Recuperar contextualmente
context_facts = client.search("TLS requirements", top_k=5)
for item in context_facts:
    print(f"[{item.score:.2f}] {item.content} (Taint: {item.taint_signature})")
```

---

## ▀▄ 9. EVOLUCIÓN NEURAL Y SOBERANÍA PARAMÉTRICA (TTT)

Para consolidar la identidad y la memoria de largo plazo del sistema, MOSKV-1 implementa un ciclo de **Test-Time Training (TTT)** descentralizado y local sobre silicio unificado (Apple Metal). Esto destila el comportamiento y los axiomas operativos directamente en pesos neuronales adaptativos (**LoRA**), manteniendo los hechos dinámicos y la memoria episódica en la capa vectorial (RAG).

### 9.1 Estructura Física del Workspace de Entrenamiento (`~/.babylon60/training/`)

El espacio físico del demonio de entrenamiento se estructura de la siguiente manera:

```
~/.babylon60/training/
├── adapters/                          # Pesos LoRA y configuraciones (Capa Crítica)
│   ├── adapters.safetensors               # 44MB — Pesos LoRA activos de producción
│   ├── adapter_config.json                # Hiperparámetros de entrenamiento (rank=8, scale=20, layers=16)
│   ├── 0000100..0000600_adapters.safetensors  # Checkpoints generados durante el ciclo de entrenamiento
│   ├── Modelfile                          # Definición del modelo en Ollama
│   └── archive/                           # Rollback y linaje de adaptadores históricos
│       └── adapters_vN/                   # Snapshots de adaptadores validados por versión
├── datasets/                          # Repositorio de datos estructurados para ajuste (SFT)
│   ├── train.jsonl                        # Datos de entrenamiento (~2.0 MB / 80%)
│   ├── valid.jsonl                        # Set de validación (~275 KB / 10%)
│   ├── test.jsonl                         # Set de prueba (~266 KB / 10%)
│   └── moskv1_dataset.jsonl               # Dataset maestro consolidado y pre-dividido
├── training_telemetry.jsonl           # Log de actividades del Daemon y telemetría de entrenamiento
└── daemon.log                         # Log de ejecución en tiempo de ejecución del demonio
```

### 9.2 Filtros de Calidad y Calibración Epistémica (ExergyGuard)

Antes de inyectar cualquier trayectoria o instrucción en el conjunto de entrenamiento (`datasets/`), los datos pasan por los siguientes cortafuegos de exergía:

1.  **ExergyGuard (Filtro Antiescoria):** Purga cualquier tipo de prosa conversacional, disculpas de LLMs o muletillas decorativas de chat.
2.  **LandauerGuard (Entropía de Shannon):** Exige una densidad mínima de información por token. Mensajes redundantes o de baja entropía son descartados instantáneamente.
3.  **AnergiSuppressor:** Evalúa 15 patrones regex rígidos para eliminar frases como `"espero que esto ayude"`, `"of course"`, `"como IA..."`.
4.  **Length Bounds:** Los límites de longitud por respuesta deben encontrarse estrictamente en `[100, 4096]` caracteres.

### 9.3 El Motor de Recompensa RLHF (`RewardEngine`)

Las trayectorias de sesión recolectadas desde la memoria episódica por el daemon son evaluadas mediante la función de recompensa:

$$R(t) = R_{\text{outcome}} - \min(|\text{actions}| \times 0.01,\; 0.1) + R_{\text{tests}} + R_{\text{confidence}}$$

*   **$R_{\text{outcome}}$ (Resultado):** $+0.5$ si es éxito (`success`), $-0.5$ si es fallo (`failure`).
*   **Penalización por Ineficiencia:** $-0.01$ por cada acción ejecutada (con un tope de $-0.1$). Premia la brevedad exergética.
*   **$R_{\text{tests}}$ (Verificación física):** $+0.5$ si los tests de unidad pasaron, $+0.1$ si al menos se ejecutaron.
*   **$R_{\text{confidence}}$ (Confianza):** $+0.1$ si la confianza promedio de la trayectoria superó el $80\%$.
*   **Umbral Dorado:** Solo trayectorias con $R(t) > 0.4$ califican como "Golden Trajectories" y son añadidas a `train.jsonl`.

### 9.4 Hiperparámetros de Entrenamiento

El ajuste local fine-tuning se ejecuta bajo los siguientes parámetros exergéticos:

*   **Modelo Base:** `Qwen2.5-Coder-7B-Instruct-4bit` (optimizado para Apple Metal).
*   **LoRA Rank ($r$):** `8` (overhead paramétrico mínimo, ~44MB por adaptador).
*   **LoRA Alpha ($\alpha$):** `20.0` (influencia agresiva del adaptador; ratio $\alpha/r = 2.5$).
*   **Capas de Atención:** `16` (cobertura en las capas de atención a lo largo del stack de transformers).
*   **Grad Checkpoint:** `true` (ahorro masivo de VRAM mediante recompilado de gradientes).
*   **Optimización de Lote:** Batch size de `1` y acumulación de gradientes de `2` (evita OOM en M1/M2/M3).
*   **Límite de Secuencia:** Max sequence length de `1280` tokens.

### 9.5 El Ciclo Nocturno del Demonio de TTT (`com.moskv1.daemon`)

El demonio de entrenamiento se ejecuta en ciclos de fondo (cada hora) orquestado por `launchd`:

```
[Inicio de Ciclo]
       │
       ▼
[Compilar Dataset Estático] ➔ Lee AGENTS.md, workflows, y Memory Vault
       │
       ▼
[Extraer Sesiones Recientes] ➔ Busca nuevas trayectorias en SQLite
       │
       ▼
[Filtrar Golden Data] ➔ Evalúa con RewardEngine (R > 0.4) y añade a train.jsonl
       │
       ▼
[Detonar mlx_lm lora] ➔ Ejecuta entrenamiento acelerado por Metal (50 iteraciones)
       │
       ▼
[Validar Adaptador] ➔ Escaneo NaN/Inf en pesos con AdapterVerifier
       │
       ▼
[Registrar y Archivar] ➔ Guarda snapshot en archive/ y actualiza el active pointer
       │
       ▼
[Hot Reload de Inferencia] ➔ MOSKV1Core recarga los pesos al vuelo sin downtime
```

### 9.6 Guía de Referencia de comandos CLI de Entrenamiento

Para interactuar manualmente con el pipeline de entrenamiento local:

```bash
# Compilar dataset combinando fuentes estáticas y base de datos
python -m babylon60.extensions.training.moskv1_cli compile --workspace .

# Ejecutar entrenamiento manual local (600 iteraciones)
python -m babylon60.extensions.training.moskv1_cli train --iters 600

# Validar integridad del dataset contra reglas ExergyGuard
python -m babylon60.extensions.training.moskv1_cli validate

# Mostrar estadísticas del volumen y balance de datos compiled
python -m babylon60.extensions.training.moskv1_cli stats

# Registrar el adaptador safetensors actual en el registro local
python -m babylon60.extensions.training.moskv1_cli register
```

---
`GUÍA DE BUEN USO DE BABYLON-60` | `PROPIEDAD DE: borjamoskv` | `LICENCIA: Apache-2.0`
