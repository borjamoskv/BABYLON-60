# 🌿 02_EDIN_SWARMS — Swarm Topologies & Agentic Architecture

> **DOMINIO SOBERANO: `edin.swarms`**  
> Invariante: **INV_C5_18 / Zero-Worktree Swarm Scaling / Manta de Markov**  
> Estatus Epistémico: **Alta Exergía (C5-REAL)**

---

## 1. Misión y Límite Epistémico (Markov Blanket)

`02_EDIN_SWARMS` constituye la tercera cámara del monorepositorio **BABYLON-60**, dedicada exclusivamente a la orquestación distribuida de enjambres multi-agente, topologías de verificación masiva (Centuria 100x / Legión) y protocolos de transducción agéntica.

```
┌─────────────────────────────────────────────────────────────┐
│                    02_EDIN_SWARMS                           │
│               (edin.swarms — Swarms)                        │
│  • Swarm Orchestrators (Kimi K3 / OpenRouter / vLLM / MLX)  │
│  • Dynamic Subagent Lifecycle & Deadlock Mitigation         │
│  • Topologies (Centuria 100x, Swarm Router, PxS Tuning)     │
│  • Protocols (PSAFE v3.0, AOF v2.0, SCITT Attestation)      │
└──────────────┬───────────────────────────────▲──────────────┘
               │ (Firma Ed25519)               │ (Diagnósticos)
               ▼                               │
┌───────────────────────────────┐ ┌────────────┴──────────────┐
│        00_ABZU_KERNEL         │ │      01_KISH_ENGINE        │
│     (babylon60.com — Ring-0)  │ │ (cortexpersist.* — Cortex) │
│  • BFT Consensus Ledger       │ │  • LSP Paracortex Server   │
│  • C-ABI SharedManifest 64B   │ │  • Verifiable Inference    │
│  • #![no_std] Rust Crates     │ │  • Multi-Modal Transducers │
└───────────────────────────────┘ └────────────────────────────┘
```

### Invariantes Estructurales de Aislamiento
1. **Aislamiento de Ring-0:** Los agentes estocásticos (LLMs) **NUNCA** tienen acceso directo de mutación sobre las estructuras de memoria del kernel (`00_ABZU_KERNEL`).
2. **Barrera BFT Mandatoria:** Toda propuesta de estado o resultado generado por un worker de un enjambre debe empaquetarse en un `AttestationEnvelope` firmado y pasar por el consenso BFT antes de persistirse.
3. **Topología PxS Anti-Thrashing:** En hardware Apple Silicon (ARM64), la concurrencia de hilos se fija a la regla empírica $P \times S$ para impedir el estrangulamiento por cambios de contexto involuntarios (`ru_nivcsw`).

---

## 2. Componentes de la Cámara

| Módulo | Propósito | Invariante Asignada |
|---|---|---|
| `orchestrator/swarm.py` | Orquestador multi-backend con circuit breaker y futex pager. | `INV_C5_18` (Zero-Worktree) |
| `orchestrator/lifecycle.py` | Máquina de estados de subagentes y watchdog anti-deadlock. | `INV_C5_TURING_CASTRATION` |
| `topologies/router.py` | Despachador central de habilidades con tolerancia a typos. | `INV_C5_ROUTER_LEVENSHTEIN` |
| `topologies/centuria.py` | Topología de verificación paralela de 100 workers. | `INV_C5_CENTURIA_BARRIER` |
| `protocols/aof.py` | Marco Operativo Agéntico (PSAFE v3.0 / AOF v2.0 / Guillotina de Hume). | `INV_C5_HUME_GUILLOTINE` |
| `protocols/attestation.py` | Sobres criptográficos SCITT / COSE_Sign1 para mensajería inter-agente. | `INV_C5_SCITT_RFC9942` |
| `clients/kimi.py` | Cliente nativo Moonshot / Kimi K3 resiliente. | `INV_C5_KIMI_AIRGAP` |
| `clients/openrouter.py` | Pasarela unificada hacia OpenRouter para modelos de frontera. | `INV_C5_OPENROUTER_ROUTING` |

---

## 3. Guía de Ejecución

```bash
# Ejecución de tests unitarios del dominio agents_archi
pytest tests/test_agents_archi.py -v

# Importación nativa en Python
python3 -c "from agents_archi import SwarmOrchestrator, SwarmConfig; print('agents_archi online')"
```
