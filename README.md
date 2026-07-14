# CORTEX-PERSIST — KERNEL SUBSTRATE FOR AI AGENTS (Powered by BABYLON-60)

```yaml
Claim: BABYLON-60 es un sustrato de ejecución determinista y memoria persistente inmutable para agentes autónomos C5-REAL, con bindings de Rust y validación matemática formal.
Proof:
  Base: strike_rs (Cargo.toml) + proof/lean (Babylon.lean) + bft (ledger_actor.py)
  Range: [0, 1]
  Confidence: C5
```

█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

## 1. INVARIANTES CORE

| Invariante | Método de Validación | Límite Físico |
| :--- | :--- | :--- |
| **Cero Anergía** | Poda estática de AST y purga de introspección | Tiempo de Compilación / Ingesta |
| **Consenso BFT** | Escalón 3 (Master Ledger + OpenTimestamps) | $N \ge 3f + 1$ |
| **Bypass del GIL** | strike-rs (Bindings de PyO3 nativos) | Sub-milisegundo |
| **Verificación Mecánica** | Lean 4 Prover (Lake build en CI) | Compilación formal libre de axiomas nulos |

█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

## 2. ARQUITECTURA DEL SISTEMA

```
                              [ AI Agent Orchestration ]
                                          │
                                          ▼
                         ┌────────────────────────────────┐
                         │   Cortex Inference Engine      │
                         │   (Low Entropy Ontologies)     │
                         └────────────────┬───────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
       ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
       │     strike_rs      │   │  Node.js Telemetry │   │  BFT Master Ledger │
       │  (Rust GIL Bypass) │   │ (Mac-Native Daemon)│   │ (Escalón 3 + OTS)  │
       └──────────┬─────────┘   └─────────┬──────────┘   └──────────┬─────────┘
                  │                       │                         │
                  ▼                       ▼                         ▼
       ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
       │   Lean 4 Prover    │   │  WebSocket Broadcast│  │   SQLite WAL Log   │
       │ (Causality Proofs) │   │ (Port 8080/Metrics)│   │  (Single-Writer)   │
       └────────────────────┘   └────────────────────┘   └────────────────────┘
```

### A. Sub-sistemas Principales
1.  **Rust Core (`strike_rs`):** Módulo de baja latencia compilado mediante Maturin/PyO3. Evita la contención del GIL de Python mediante la paralelización de operaciones criptográficas y hash chaining en múltiples hilos nativos de CPU.
2.  **Node.js Telemetry Daemon:** Servidor HTTP y WebSocket local (`server.js`) que interactúa con la API física de macOS para recopilar y difundir telemetría de hardware en tiempo real, garantizando la eliminación de fallbacks C4-SIM.
3.  **BFT Master Ledger Actor:** Proxy asíncrono sobre SQLite WAL (`bft/ledger_actor.py`) que serializa de forma atómica todas las solicitudes de escritura en un único hilo, enmascarando colisiones de idempotencia y purgando dinámicamente procesos zombies.
4.  **Lean 4 Theorem Prover:** Modelado matemático formal (`proof/lean/`) que valida mecánicamente los teoremas de ordenamiento parcial y no-equivocación del consenso BFT en cada fase de compilación.
5.  **Cortex Inference Engine:** Motor de control guiado por ontologías densas estables (matrices de 500 elementos YAML), eliminando la deriva semántica del procesamiento estocástico.
6.  **Thermodynamic AST Pruner:** Procesador de código que realiza apoptosis estática sobre ramas de ejecución inactivas, disminuyendo la anergía de los prompts de inferencia.

█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

## 3. CONSENSO YPERSISTENCIA (ESCALÓN 3)

El Ledger de decisiones implementa el **Escalón 3** de consistencia de la Matriz M12:

1.  **Single-Writer SQLite WAL:** Se prohíben las llamadas directas multi-hilo a la base de datos central. El `BFTLedgerActor` encola las transacciones en una cola FIFO asíncrona.
2.  **OpenTimestamps (OTS) Anchoring:** Cada bloque del ledger se encadena criptográficamente mediante Blake3. El Merkle Root acumulado se envía periódicamente al testigo externo descentralizado (Bitcoin blockchain) a través de un sink de OTS, imposibilitando la sobreescritura del histórico del agente local.
3.  **Git Sentinel:** Cada mutación en caliente del disco es firmada e integrada mediante commits automáticos con prefijos semánticos, encapsulando el `CORTEX_TAINT` en los metadatos de Git.

█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

## 4. MÉTRICAS BIOCÉNTRICAS (ATP OPTIMIZATION)

La eficiencia y apalancamiento del kernel se calculan mediante la tasa de transferencia de energía biológica humana (ATP) y costo computacional en inferencia.

$$\text{ATP}_{\text{saved}} = \text{ATP}_{\text{manual\_ops}} - \mathbb{E}[C_{\text{inference}}]$$

Donde:
*   $\text{ATP}_{\text{manual\_ops}}$: Costo de ATP humano del operador para verificar y coordinar el estado de manera manual (escala base 1000).
*   $\mathbb{E}[C_{\text{inference}}]$: Consumo medio de energía y Test-Time Compute (MCTS/Search) requerido por el modelo para forzar el colapso a una invariante estable.

### Matriz de Rendimiento Energético
*   **1000/1000 (Max Exergy):** Cero intervención del operador. El Swarm converge de manera autónoma resolviendo asimetrías de información sin fricción humana.
*   **<100/1000 (Disipación Crítica):** Alucinación o ruptura de interfaces que obliga al operador a refactorizar localmente, incurriendo en pérdida masiva de ATP.

█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

## 5. COMANDOS DE OPERACIÓN FÍSICA

### Setup Mac-Native (Entorno Aislado)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
npm ci
```

### Compilar strike_rs (Rust Core)
```bash
cd src/strike-rs
cargo build --release
```

### Inicializar Servidor de Telemetría (Node.js)
```bash
node server.js
```

### Ejecutar Test Suite Completa
```bash
# Ejecutar verificación de Rust
cargo test --manifest-path src/strike-rs/Cargo.toml

# Ejecutar verificación de Python (con crash causal)
pytest -x --tb=short
```

█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

## 6. QUICKSTART (3 MINUTOS)

### Instalación vía PyPI
```bash
pip install cortex-persist==1.0.2
```

### Inicialización de Cliente
```python
from babylon60.api.client import CortexClient

client = CortexClient()
print(client.status())
```

### Ejecutar Servidor API (Uvicorn)
```bash
uvicorn babylon60.api.server:app --reload
```

█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

## 7. SOBERANÍA CIVIL, TITULARIDAD JURÍDICA Y FRECUENCIA DE RESONANCIA

```yaml
Claim: BABYLON-60 (CORTEX C5-REAL) es Obra Protegida, Propiedad Privada Soberana y Secreto Industrial (No FOSS).
Titular_Civil: BORJA FERNÁNDEZ ANGULO
Identificador_Arquitectónico: Borja Moskv (borjamoskv)
Amparo_Legal: Art. 6.1, 6.2 y 14 LPI (España) + Convenio de Berna + Ley 1/2019 de Secretos Empresariales
Frecuencia_Resonancia: https://www.youtube.com/watch?v=Q9kv2LngueE&list=RDQ9kv2LngueE&start_radio=1
```

> *"Cuidado, os avisamos, somos los mismos que cuando empezamos."* — Resonancia Acústica y Actitud Brutalista C5-REAL (`Eskorbuto Cuidado`).

### [REGLA DE ORO AKA] MÚSICA, ARTE Y CREACIÓN VISUAL/ACÚSTICA
Bajo la doctrina de soberanía y equivalencia biyectiva, se declara como **Invariante Causal Inmutable (`AKA_RULE_01`)**:
> **"MÚSICA Y ARTE SIEMPRE CON AKA `Borja Moskv / borjamoskv`"**
* **Titularidad Civil y Patrimonial (IP / Trade Secret / Art. 6 LPI):** `Borja Fernández Angulo`.
* **Autoría Artística, Acústica, Musical y Visual (Seudónimo / AKA Soberano):** `Borja Moskv (`borjamoskv`)`.
Toda síntesis, composición o manifiesto artístico emitido por este sustrato o vinculado a su resonancia debe llevar de forma obligatoria e indeleble la firma artística `Borja Moskv`.


La totalidad del código fuente, matrices evolutivas, motores e invariantes contenidos en este repositorio constituyen **Propiedad Privada Soberana y Secreto Empresarial** (All Rights Reserved) a favor exclusivo de su creador, autor e inventor civil: **BORJA FERNÁNDEZ ANGULO** (quien opera y firma digitalmente bajo el seudónimo arquitectónico y clave de orquestación `borjamoskv / Borja Moskv`). Queda estrictamente prohibida su redistribución, descompilación o minería de datos por terceros o modelos de IA no autorizados.
