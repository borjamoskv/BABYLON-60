# 🌿 02_EDIN_SWARMS — Swarm Topologies & Agentic Architecture

> **DOMINIO SOBERANO: `edin.swarms`**  
> Invariante: **INV_C5_18 / Zero-Worktree Swarm Scaling / Manta de Markov**  
> Estatus Epistémico: **Alta Exergía (C5-REAL)**

---

## 1. Misión y Límite Epistémico (Markov Blanket)

`02_EDIN_SWARMS` constituye la tercera cámara del monorepositorio **BABYLON-60**, dedicada exclusivamente a la orquestación distribuida de enjambres multi-agente, topologías de verificación masiva (SHARUR-3600 / Edin 100x) y protocolos de transducción agéntica bajo el dominio canónico `edin.swarms`.

```
┌─────────────────────────────────────────────────────────────┐
│                    02_EDIN_SWARMS                           │
│               (edin.swarms — Anillo-2)                      │
│  • Swarm Orchestrators (vLLM / MLX / OpenRouter)            │
│  • Dynamic Subagent Lifecycle & Deadlock Mitigation         │
│  • Topologies (SHARUR-3600 Matrix, Swarm Router, PxS)       │
│  • Protocols (PSAFE v3.0, AOF v2.0, SCITT Attestation)      │
└──────────────┬───────────────────────────────▲──────────────┘
               │ (Firma Ed25519)               │ (Diagnósticos)
               ▼                               │
┌───────────────────────────────┐ ┌────────────┴──────────────┐
│        00_ABZU_KERNEL         │ │       01_KISH_ENGINE       │
│    (abzu.kernel — Anillo-0)   │ │  (kish.engine — Anillo-1)  │
│  • BFT Consensus Ledger       │ │  • LSP Paracortex Server   │
│  • C-ABI SharedManifest 64B   │ │  • Verifiable Inference    │
│  • #![no_std] Rust Crates     │ │  • Multi-Modal Transducers │
└───────────────────────────────┘ └────────────────────────────┘
```

### Perfiles SHARUR y concurrencia

SHARUR-3600 designa el modelo sexagesimal de direccionamiento (60²), no una
promesa de 3600 agentes simultáneos. [EdinTopology](agents_archi/topologies/edin.py)
configura entre 1 y 100 workers; la concurrencia efectiva del planificador es
`min(worker_count, max_batch_concurrency)` (100 y 16 por defecto).
Una función síncrona ya iniciada puede seguir ejecutándose tras el timeout
de su espera; esta cota no acredita un límite físico global de hilos o llamadas.

| Perfil | Qué describe la fuente | Referencia |
| --- | --- | --- |
| 21 | Workers configurados para una campaña | [Script](../scripts/c5_sharur/sharur_21_agentes.py) |
| 100 | Simulación de tareas; perfil EDIN configurable; campaña separada con evidencia parcial | [Simulación](../scripts/sharur/run_sharur_3600.py), [CLAIMS](../CLAIMS.toml) |
| 222 | 220 workers y dos coordinadores declarados | [Topología](../docs/04_research/sharur_222_swarm_topology.md) |
| 1000 | Simulación de tareas, no 1000 agentes LLM ejecutados | [Script](../scripts/sharur/run_sharur_1000.py) |
| 10000 | Objetivo de diseño CTA | [Especificación](../docs/10_sharur_swarm_cta_spec.md) |

Registrar por campaña tareas, concurrencia configurada y observada, tipo de
worker (real o simulado) y recibo. No extrapolar el alcance del claim
`sharur_100_swarm_concurrency` a otros perfiles.

### Invariantes Estructurales de Aislamiento
1. **Aislamiento de Ring-0:** Los agentes estocásticos (LLMs) **NUNCA** tienen acceso directo de mutación sobre las estructuras de memoria del kernel (`00_ABZU_KERNEL`).
2. **Separación de propuesta y autorización:** Un resultado de worker es una propuesta, no autoridad de commit. El flujo de atestación y validación depende del componente y del efecto; esta descripción no acredita que todos los resultados pasen por un protocolo BFT distribuido. LARSA-120 designa el quórum heterogéneo local descrito en el [manifiesto](../ARCHITECTURE_MANIFEST.md#0-nomenclatura-y-alcance).
3. **Topología PxS Anti-Thrashing:** La regla $P \times S$ es una heurística de diseño para dimensionar perfiles; no una garantía de ausencia de thrashing. El planificador EDIN usa su propio límite de concurrencia configurable, y las mediciones de `ru_nivcsw` deben atribuirse a la campaña y al hardware correspondientes.

---

## 2. Componentes de la Cámara (`02_EDIN_SWARMS/agents_archi/`)

Los módulos siguientes residen bajo el paquete Python `02_EDIN_SWARMS/agents_archi/` (junto con los adaptadores en `02_EDIN_SWARMS/adapters/`):

| Módulo | Propósito | Invariante Asignada |
|---|---|---|
| `orchestrator/swarm.py` | Orquestador multi-backend con circuit breaker y futex pager (`edin.swarms`). | `INV_C5_18` (Zero-Worktree) |
| `orchestrator/lifecycle.py` | Máquina de estados de subagentes y watchdog anti-deadlock. | `INV_C5_TURING_CASTRATION` |
| `topologies/router.py` | Despachador central de habilidades con tolerancia a typos. | `INV_C5_ROUTER_LEVENSHTEIN` |
| `topologies/edin.py` | Topología EDIN de verificación paralela (hasta 100 workers configurados; límite de planificación independiente). | `INV_C5_EDIN_BARRIER` |
| `protocols/aof.py` | Marco Operativo Agéntico (PSAFE v3.0 / AOF v2.0 / Guillotina de Hume). | `INV_C5_HUME_GUILLOTINE` |
| `protocols/attestation.py` | Sobres criptográficos SCITT / COSE_Sign1 para mensajería inter-agente. | `INV_C5_SCITT_RFC9942` |
| `clients/openrouter.py` | Pasarela unificada hacia OpenRouter para modelos de frontera. | `INV_C5_OPENROUTER_ROUTING` |

---

## 3. Guía de Ejecución

```bash
# Ejecución de tests unitarios y de concurrencia de 100 workers (CLAIMS.toml: sharur_100_swarm_concurrency)
uv run --locked pytest tests/test_agents_archi.py tests/test_swarm_100_concurrency.py -q

# Importación nativa en Python
uv run --locked python3 -c "from agents_archi import SwarmOrchestrator, SwarmConfig; print('edin.swarms online')"
```
