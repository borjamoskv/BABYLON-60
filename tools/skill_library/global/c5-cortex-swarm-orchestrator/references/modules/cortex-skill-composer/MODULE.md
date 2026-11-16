---
name: cortex-skill-composer
display_name: Componedor & Orquestador de Cadenas de Skills
description: Composición y orquestación en cadena (Skill Chains) de múltiples habilidades CORTEX. Dispara con "componer skills", "skill chain", "cadena de habilidades", "pipeline de skills", "cortex skill composer", "orquestación de habilidades", "skill pipeline".
role: arquitecto
allowed_roles:
- arquitecto
- ejecutor
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# Skill: Cortex Skill Composer (Composición Funtorial $F \circ G$)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `arquitecto` (Arquitecto (Diseño Sistémico & Contratos de Invariantes))
> - **Modo de Acceso a Worktree:** `spec-only` (spec-only (Lectura profunda y modelado formal; emisión de especificaciones sin mutación de código de producción))
> - **Fase Causal:** `design`
> - **Contrato Handoff:** Recibe de `operador` $\to$ Despacha a `ejecutor`

Este protocolo permite componer múltiples habilidades en **cadenas de procesamiento funtorial**, garantizando que el output de cada fase se transforme sin pérdida de exergía hacia la siguiente.

---

## 1. Cadenas Canónicas Pre-definidas

Cuando el operador solicita un flujo complejo, el orquestador DEBE seleccionar o instanciar una de las siguientes cadenas canónicas:

```mermaid
graph LR
    subgraph Ω-Synthesis
        DR["autodidact-omega-deep-research"] --> PCS["polymath-concept-synthesis"] --> APA["agentic-protocol-axiomatization"]
    end
    subgraph Ω-Falsification
        PCS2["polymath-concept-synthesis"] --> DPF["discourse-popperian-falsification"]
    end
    subgraph Ω-Audit
        CT["cortex-telemetry"] --> CSA["cortex-skill-auditor"]
    end
    subgraph Ω-Swarm-Pipelines
        EGA["existence-gap-audit"] --> LA["legion-audit"] --> APP["anergy-purge-protocol"]
        LSP["lora-swarm-pipeline"] --> WFA["writing-for-agents"]
        SQC["swarm-quantum-collapse"] --> CDS["c5-real-devsecops-scaffold"]
    end
    subgraph Ω-Bounty-Ingest
        BFT["bounty-feed-transducer"] --> EXF["exergy-filter"] --> BRD["bounty-ring-dispatcher"]
        BRD --> DBS["defi-bytecode-scraper"]
        BRD --> WMA["webkit-memory-audit"]
        BRD --> S1M["saga1-ml-sentinel"]
    end
```

### 1.1. Cadena Ω-Synthesis (Cristalización Ontológica Completa)
- **Secuencia**: `autodidact-omega-deep-research` $\to$ `polymath-concept-synthesis` $\to$ `agentic-protocol-axiomatization`
- **Uso**: Investigación profunda desde cero, proyectada a través de disciplinas y axiomatizada formalmente.

### 1.2. Cadena Ω-Falsification (Síntesis + Falsación Inmediata)
- **Secuencia**: `polymath-concept-synthesis` $\to$ `discourse-popperian-falsification`
- **Uso**: Formular un concepto en 6 disciplinas e inmediatamente someterlo a prueba popperiana de contraejemplos.

### 1.3. Cadena Ω-Legal (Análisis LegalTech + Falsación Epistémica)
- **Secuencia**: `c5-real-legaltech-analysis` $\to$ `discourse-popperian-falsification`
- **Uso**: Auditar plataformas o leyes, identificando anergía normativa y buscando falsación empírica.

### 1.4. Cadena Ω-Audit (Telemetría + Meta-Auditoría de Skills)
- **Secuencia**: `cortex-telemetry` $\to$ `cortex-skill-auditor`
- **Uso**: Extraer métricas de uso históricas y auditar la eficiencia exergética de las habilidades utilizadas.

### 1.5. Cadenas Ω-Swarm (Enjambres Multicapa C5-REAL)
- **Ω-Swarm-Audit**: `existence-gap-audit` $\to$ `legion-audit` $\to$ `anergy-purge-protocol` (Auditoría de existencia $\to$ enjambre de 100 workers $\to$ purga de anergía).
- **Ω-Swarm-Mining**: `lora-swarm-pipeline` $\to$ `writing-for-agents` (Minería N-Zonas $\to$ síntesis para agentes).
- **Ω-Swarm-Sync**: `swarm-quantum-collapse` $\to$ `c5-real-devsecops-scaffold` (Colapso cuántico git P×S $\to$ verificación DevSecOps Zero-Trust).

### 1.5. Cadena Ω-Genesis (Telemetría + Síntesis Predictiva)
- **Secuencia**: `cortex-telemetry` $\to$ `cortex-skill-genesis`
- **Uso**: Analizar patrones de prompts no cubiertos y sintetizar automáticamente nuevos `SKILL.md`.

### 1.6. Cadena Ω-Bounty-Ingest (Ingestión Funtorial de Bounties $\to$ Lock-Free Ring)
- **Secuencia**: `bounty-feed-transducer` $\to$ `exergy-filter` $\to$ `bounty-ring-dispatcher` ($\to$ `defi-bytecode-scraper` $\lor$ `webkit-memory-audit` $\lor$ `saga1-ml-sentinel`)
- **Uso**: Ingestión continua y triaje causal de superficies de ataque desde feeds públicos (Immunefi, Huntr, Code4rena, GitHub Advisories) acoplados al orquestador lock-free de BABYLON-60 bajo `INV_C5_SHM`.

---

## 2. Protocolo de Ejecución Funtorial

1. **Analizar la Demanda**: Determinar la lista ordenada de habilidades $[S_1, S_2, \dots, S_n]$.
2. **Heredar Invariantes de KERNEL**: Garantizar que la salida de $S_i$ cumple con los axiomas en [KERNEL.md](../../../../KERNEL.md).
3. **Mapeo de Salida-Entrada**: El artefacto o respuesta resultante de $S_i$ actúa como objeto de la categoría origen para $S_{i+1}$.
4. **Verificación de Cierre**: Emitir una síntesis final notificando los eslabones ejecutados y el delta de exergía logrado.
