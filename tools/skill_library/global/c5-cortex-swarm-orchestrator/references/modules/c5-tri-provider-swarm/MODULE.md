---
name: c5-tri-provider-swarm
display_name: Orquestador de Enjambre Híbrido Tri-Provider (OpenAI ⊗ Qwen ⊗ Local vLLM/MLX)
description: Orquestación desacoplada de enjambres multi-agente combinando OpenAI (Planner N0, Structured Outputs), Qwen (Workers de Código N1 en vLLM local sin 429) y un modelo local de contexto largo (Arqueología N2 en vLLM/MLX) bajo semáforos de Landauer. Dispara con "enjambre híbrido", "tri provider swarm", "orquestador tres modelos", "tri-provider swarm".
role: ejecutor
allowed_roles:
- ejecutor
- arquitecto
directives:
  worktree_mode: read-write
  phase: implementation
  handoff:
    upstream: arquitecto
    downstream: auditor
---

# 🐝 Skill: Orquestador de Enjambre Híbrido Tri-Provider (C5-REAL)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `ejecutor` (Ejecutor (Implementación en Silicio & Mutación de Árbol de Trabajo))
> - **Modo de Acceso a Worktree:** `read-write` (Mutación atómica de archivos, compilación, ejecución de tests locales y generación de artefactos)
> - **Fase Causal:** `implementation`
> - **Contrato Handoff:** Recibe de `arquitecto` $\to$ Despacha a `auditor`

Este protocolo formaliza el despacho de enjambres multi-agente masivos ($P \times S$) desacoplando las tareas según la ventaja comparativa de los tres niveles de inferencia, eliminando los cuellos de botella de saturación de cuota (`HTTP 429`) y coste financiero.

---

## 1. La Tríada Óptima C5-REAL

```
                      ┌────────────────────────────────────────┐
                      │            TAREA / MISIÓN             │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │    NIVEL 0: PLANNER & VALIDADOR        │
                      │    OpenAI (GPT-4o / o3-mini)           │
                      │    • Strict Structured Outputs (Zod)   │
                      │    • Emisión del DAG de Subtareas      │
                      └──────────────────┬─────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │   VÁLVULA DE CONCURRENCIA DE LANDAUER  │
                      │   (AgentPager PxS · asyncio.Semaphore) │
                      └──────────┬───────────────────┬─────────┘
                                 │                   │
                ┌────────────────┘                   └────────────────┐
                ▼                                                     ▼
┌────────────────────────────────────────┐         ┌────────────────────────────────────────┐
│   NIVEL 1: WORKERS DE CÓDIGO BARE-METAL│         │   NIVEL 2: ARQUEOLOGÍA DE MONORREPOS   │
│   Qwen 2.5-Coder-32B (Local vLLM / MLX)│         │   Contexto largo local (vLLM o MLX)    │
│   • Cero coste marginal por token      │         │   • Ventana acotada por modelo y VRAM  │
│   • Inmune a Rate Limits (429)         │         │   • Objetivo: ingesta en loopback      │
│   • Latencia TTFT sub-100ms            │         │   • Fallback a Qwen si falla           │
└──────────────────┬─────────────────────┘         └──────────────────┬─────────────────────┘
                   │                                                  │
                   └─────────────────────┬────────────────────────────┘
                                         │
                                         ▼
                      ┌────────────────────────────────────────┐
                      │        REDUCTOR DE ANERGÍA & SELLO     │
                      │    BABYLON-60 / KUDURRU-64 / Touch ID  │
                      │    • Veto determinista en silicio      │
                      │    • Recibos SCITT RFC 9942 COSE_Sign1 │
                      └────────────────────────────────────────┘
```

---

## 2. Reglas de Despacho y Enrutamiento de Tareas

1. **Nivel 0 · Planificación y Tipos Estrictos $\to$ OpenAI:**
   - Todo esquema de descomposición de tareas que deba colapsar en un DAG sin errores sintácticos se despacha a OpenAI utilizando `strict: true` en el esquema JSON.
2. **Nivel 1 · Fan-Out Concurrente Masivo (Legión 100) $\to$ Qwen Local (vLLM / MLX):**
   - La generación de código, refactorización masiva, linters de AST y ejecución de tests se delegan exclusivamente a instancias locales de **Qwen 2.5-Coder**.
   - **Invariante:** Cero llamadas a APIs de pago por token para mutaciones iterativas masivas.
3. **Nivel 2 · Exploración de Contexto Masivo (por encima de la ventana de los workers) $\to$ Modelo Local de Contexto Largo (vLLM / MLX):**
   - La ingesta de repositorios enteros, dumps de logs forenses o expedientes documentales no fragmentables se envía a un modelo local de contexto largo servido por vLLM o MLX; su ventana la fijan el modelo cargado y la memoria disponible.
4. **Válvula de Concurrencia (Anti-Thrashing):**
   - Semáforo para APIs cloud: $P_{\text{cloud}} \le 15$ concurrentes para evitar `HTTP 429`.
   - Semáforo para hardware local: $P_{\text{local}} \le 64$ acoplado a la VRAM disponible.
5. **Conmutación Dinámica por Error (Failover):**
   - Si el modelo local de contexto largo devuelve timeout o la entrada excede su ventana, la tarea conmuta automáticamente a fragmentación en Qwen Local.
   - Si OpenAI satura cuota (`429`), conmuta temporalmente a Qwen-Max en DashScope con prefijo estricto.

---

## 3. Código del Arnés de Ejecución

El despachador ejecutable reside en:
`../../../../c5-tri-provider-swarm/scripts/tri_swarm_dispatcher.py`

Puede invocarse directamente desde Python o mediante scripts CLI:
```bash
python3 ../../../../c5-tri-provider-swarm/scripts/tri_swarm_dispatcher.py --tasks tasks.json
```
