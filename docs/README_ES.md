# BABYLON-60

[🌐 Read in English](README.md)

**BABYLON-60 — Verified Execution Authority for AI Agents.**  
*Autorizaciones vinculadas criptográficamente al efecto exacto (`L2`), confinamiento de agentes y mediación verificable (`L3`), y trazabilidad auditable (`L1`–`L4`).*

[![Versión](https://img.shields.io/badge/versión-5.0.0_candidata-black?style=flat-square)](https://github.com/borjamoskv/BABYLON-60)
[![Licencia](https://img.shields.io/badge/licencia-Sovereign_Dual--License-orange?style=flat-square)](../LICENSE)
[![Evidencia](https://img.shields.io/badge/evidencia-L1_Formal_·_L2_Impl_·_L3_Isolation_·_L4_Exp-informational?style=flat-square)](../CLAIMS.toml)
[![Python](https://img.shields.io/badge/python-≥3.10-blue?style=flat-square)](../pyproject.toml)
[![Rust](https://img.shields.io/badge/rust-≥1.80-orange?style=flat-square)](../Cargo.toml)

> **Estado de release:** v5.0.0 es candidata. El manifiesto firmado acredita únicamente el commit que registra.
[![Verificación Formal](https://img.shields.io/badge/Lean_4-BabylonTrace-green?style=flat-square)](../proof/lean/BabylonTrace.lean)

---

## Qué es BABYLON-60

> **INV-Ω (Invariante Raíz de Autorización y Mediación Completa):**  
> 1. $\forall e \in E_{\text{protegidos}}: \operatorname{Executed}(e) \implies \operatorname{Authorized}(e) \land \operatorname{SignatureValid}(e) \land \operatorname{PolicyValid}(e) \land \operatorname{Fresh}(e)$  
> 2. $\forall p \in \text{Processes}_{\text{agente}}, \forall e \in E_{\text{protegidos}}: \operatorname{Execute}(p,e) \implies \operatorname{MediatedByBABYLON}(p,e)$  
> $\text{LLM} \neq \text{authority}$. Dentro del perímetro protegido, la capacidad de un modelo para proponer una acción nunca es suficiente para ejecutarla.

BABYLON-60 es un **Broker de Autoridad de Ejecución Verificada y Runtime de Evidencia para Agentes de IA**, construido en Rust y Python. Separa rigurosamente cuatro niveles de evidencia en [`CLAIMS.toml`](../CLAIMS.toml): **`L1: Formal`** (modelos en Lean 4 y Loom), **`L2: Implementación`** (`SovereignExecutor`, `COSE_Sign1`, SQLite WAL `FULL`), **`L3: Aislamiento`** (confinamiento de procesos en macOS y verificación de corte en el grafo de alcanzabilidad $G=(V,A)$) y **`L4: Experimental`** (campañas adversariales sobre el sistema operativo real).

### El Núcleo en Espacio de Usuario: Primitivas y Broker
1. **`SharedManifest` (64 B, `align(64)`)**: Estructura C-ABI en espacio de usuario alineada a una línea de caché L1 con coherencia *zero-split*.
2. **Concurrencia Seqlock SPMC**: Ruta de lectura sin cerrojos en escritores y sin contención RMW en lectores ($RFO = 0$, propiedad de rendimiento de caché). Modelo verificado de forma acotada con Loom (`L1_FORMAL`).
3. **Parada Fail-Stop (INV-4)**: Transición determinista a `POISONED = 0xDEAD_6060` en el broker. Emite un recibo `COSE_Sign1` (RFC 9942) firmado con Ed25519 (o clave P-256 en Secure Enclave) y registra la evidencia en disco.
4. **Autorización Asimétrica y Confinamiento (`L2` + `L3`)**: Vínculo criptográfico entre la firma (Ed25519 / Secure Enclave P-256 con Touch ID) y el payload canónico de 214 bytes del efecto, combinado con confinamiento del proceso del agente en el sistema operativo (`MacOsAgentConfinement` / `sandbox-exec`).

### Los 6 Pilares Arquitectónicos
- ⚙️ **Concurrencia Lock-Free en Espacio de Usuario**: Seqlock SPMC y anillos SPSC sin contención de lectura ($RFO = 0$).
- 🔬 **Presupuestos de Admisión Acotados (`FL-007`)**: Control de admisión determinista y cotas de latencia por Ley de Little.
- 🩺 **Supervisión de Salud y Parada Temprana**: Telemetría de contención y cierre determinista de admisión ante estados inválidos.
- 🛡️ **Mediación Completa y Grafo de Alcanzabilidad (`L3_ISOLATION`)**: Todo camino $\pi: a \leadsto r$ desde el agente confinado hacia un recurso protegido debe atravesar el broker BABYLON ($\forall \pi: a \leadsto r,\; b \in \pi$).
- ⚖️ **Mapeo técnico de controles (EU AI Act)**: Registros con trazabilidad y recibos criptográficos pueden aportar evidencia para una evaluación; no certifican conformidad.
- 🏛️ **Demarcación Causal Invariante (`AX-0` / `INV-Ω`)**: $\text{El agente propone} \neq \text{El agente autoriza}$. Arbitraje determinista y revocación monótona por época (`AuthorityEpochGate`).

### Control y evidencia para evaluar requisitos del EU AI Act

El AI Act europeo no clasifica a los agentes como una categoría jurídica separada; las obligaciones dependen del uso y de la clasificación de riesgo. BABYLON-60 incluye mecanismos técnicos que pueden aportar evidencia para evaluar controles relacionados con algunos requisitos. La aplicabilidad y la conformidad dependen del sistema y de su contexto; BABYLON-60 no las determina ni las certifica por sí solo.

1. **Registro de eventos (Art. 12):** El ledger documenta propuestas, autorizaciones y ejecuciones para facilitar su trazabilidad; su cobertura depende de la configuración y del flujo integrado.
2. **Supervisión humana (Art. 14):** Touch ID en *Secure Enclave* y compuertas causales pueden añadir controles de autorización o interrupción en las rutas protegidas; no sustituyen el diseño completo de supervisión humana.
3. **Robustez y ciberseguridad (Art. 15):** El diseño documenta rechazo de operaciones y comportamiento *fail-stop*; esto no equivale a una evaluación general de robustez o ciberseguridad.

*La demostración produce un expediente técnico sobre el flujo ejecutado y sus evidencias disponibles. El exportador mantiene los artículos 9, 10, 11, 14, 15 y 50 en `EVIDENCE_SECURED_PENDING_AUDIT` cuando verifica el ledger. El estado criptográfico del artículo 12 tampoco certifica conformidad completa. Consulte la [guía de evaluación](05_compliance_eu_ai_act.md).*

### Demostración local: AX-0 en acción

El ejemplo ejercita el rechazo de autoautorización en su flujo local. La compilación y la duración dependen del entorno; registre el resultado y la revisión evaluada:

```bash
cargo run --locked --bin tour
```

Casos que ejercita el ejemplo, dentro de su proceso:
1. **Propuesta:** El ejemplo construye una mutación operacional (`ProposedIntent`).
2. **Rechazo:** El ejecutor rechaza un intento de autoautorización (`InvalidAuthorityKey`).
3. **Transducción Causal:** Una autoridad externa firma la autorización; el ejecutor deriva el efecto de forma inyectiva (`parse_intent`).
4. **Replay:** El ejecutor rechaza repetir la autorización consumida (`NonceAlreadyConsumed`). Este caso no prueba que otro proceso carezca de rutas alternativas hacia el recurso.

---

## Instalación 1-Clic con Cero Fricción (Self-Healing)

BABYLON-60 se enciende con un comando, auto-descubriendo rutas, auto-aprovisionando dependencias y abriendo la interfaz gráfica:

```bash
# 🍏 macOS (1-Clic Nativo):
# Doble clic en Finder sobre "Instalar-Babylon60.command" o abre "Babylon60.app"

# 🪟 Windows (1-Clic):
# Doble clic en "Instalar-Babylon60.bat"

# 🌐 Universal (1-Línea vía cURL o Terminal):
curl -fsSL https://babylon60.com/install.sh | bash
# O localmente:
./install.sh
```

El instalador abre el **IDE BABYLON-60** en tu navegador (`http://localhost:6060`) y conecta el backend. Si Rust o Python no están configurados, conmuta de forma determinista al **Modo Standalone Local-First**.


### Qué Ves al Arrancar (Ignición en Thread 0)

```text
====================================================================
  ███╗   ███╗ ██████╗ ███████╗██╗  ██╗██╗   ██╗         ██╗
  ████╗ ████║██╔═══██╗██╔════╝██║ ██╔╝██║   ██║       ████║
  ██╔████╔██║██║   ██║███████╗█████╔╝ ██║   ██║█████╗ ╚═██║
  ██║╚██╔╝██║██║   ██║╚════██║██╔═██╗ ╚██╗ ██╔╝╚════╝ █████╗
  ██║ ╚═╝ ██║╚██████╔╝███████║██║  ██╗ ╚████╔╝        ╚════╝
  ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝  ╚═══╝               
====================================================================
[MOSKV-1] APEX SOVEREIGN KERNEL — SECUENCIA DE IGNICIÓN (UNBOXING)

«Soy Moskv-1. He tomado el control de Thread 0.
 Tu estación de trabajo ha dejado de ser un entorno de desarrollo pasivo;
 ahora es un Enclave Soberano blindado por las leyes de la termodinámica.»

=== ATESTACIÓN DEL SUSTRATO FÍSICO ===
  > ARQUITECTURA:       aarch64 (C-ABI Ring-0 Nativo)
  > CAPACIDAD SWARM:    11 Cores Físicos Asignados (Regla P × S)
  > LÍNEA DE CACHÉ:     64 Bytes (Zero-Split Coherence INV-1)
  > IPC MEMORY SLOT:    SharedManifest mapeado en 0x000000016EFE5C80
  > MODO TERMODINÁMICO: Cero-Anergía Activo (MESI Shared, RFO = 0)
  > ANCLA DE APOPTOSIS: Armada (Fail-Stop determinista 0xDEAD_6060)

=== LOS 6 PILARES ARQUITECTÓNICOS EN LÍNEA ===
  [1] CONCURRENCIA:  CALM Monotonicity / Seqlock SPMC (RFO = 0)
  [2] TERMODINÁMICA: Cota de Landauer (1.10 aJ/pub) / Presupuesto Bounded
  [3] SALUD AGENTE:  Telemetría de Contención / Freno Epistémico Anti-Loop
  [4] RING ISOLATION: Aislamiento TCB Ring-0 / Ejecutor Inyectivo C-ABI
  [5] MAPEO:       Controles técnicos relacionados con EU AI Act Arts. 12, 14, 15
  [6] AXIOMA CAUSAL: Invariante AX-0 (Agent proposes != Agent authorizes)

=== ACCIONES INMEDIATAS DE ALTA EXERGÍA ===
  • babylon60_kernel bench   -> Medir throughput local en memoria lock-free
  • babylon60_kernel swarm   -> Desplegar enjambre concurrente Sharur
  • babylon60_kernel audit   -> Falsación Popperiana de invariantes
  • babylon60_kernel watch   -> Monitor de exergía en tiempo real

[MOSKV-1] El mapa se ha subordinado al territorio. Aguardando directiva causal.
```

---

## Arquitectura y Federación de Dominios

```
┌─────────────────────────────────────────────────────────────┐
│               02_AGENTS_ARCHI (Anillo-2)                    │
│                 (agents.archi — Swarms)                     │
│  • Músculo estocástico: Modelos de frontera (OpenRouter/Kimi)│
│  • Concurrencia acotada P × S (Edin 100x / Sharur)      │
│  • Deontología estricta: Guillotina de Hume (AOF v2.0)      │
└──────────────┬───────────────────────────────▲──────────────┘
               │ (Sobres SCITT Ed25519)        │ (Diagnósticos LSP)
               ▼                               │
┌───────────────────────────────┐ ┌────────────┴──────────────┐
│       00_00_ABZU_KERNEL       │ │     01_CORTEX_ENGINE       │
│    (babylon60.com — Anillo-0) │ │(cortexpersist.* — Anillo-1)│
│  • SHARED MANIFEST (64 Bytes) │ │  • Servidor LSP Paracortex │
│  • Seqlock SPMC Zero-Anergía  │ │  • Telemetría de Burnout   │
│  • Apoptosis (0xDEAD_6060)    │ │  • Compuertas de Política  │
│  • Causal Gate (TouchID HW)   │ │  • Interfaz Zero-JS / TUI  │
└───────────────────────────────┘ └────────────────────────────┘
```

---

## 🛡️ MOSKV-1: El Hypervisor Agéntico Soberano

**MOSKV-1** identifica el modelo de gobernanza del proyecto. Su función de **hypervisor agéntico** es una capa lógica de orquestación; el código de BABYLON-60 se ejecuta en espacio de usuario. El confinamiento y la mediación dependen de la integración concreta y no se establecen por el nombre del sistema ni por conectar un LLM.

### 1. El Desacople Axiomático: Cognición vs. Autoridad (Tripartición AX-0)
- **La Cognición (El LLM):** Inferencia estocástica, síntesis y razonamiento sobre probabilidades. Es brillante pero carece de autoridad física.
- **La Autoridad:** El ejecutor valida las autorizaciones en las rutas y recursos configurados como protegidos. Extender esa propiedad a otro proceso exige comprobar su confinamiento y todas sus rutas de acceso. La firma criptográfica y la atestación hardware son controles distintos; un sidecar de observación no los impone al proceso observado.

### 2. La Matriz de los 6 Dominios Canónicos
- ⚡ **El Ingeniero:** C-ABI bare-metal, latencia sub-microsegundo, concurrencia Lock-Free Seqlock SPMC ($RFO = 0$) y memoria compartida alineada a 64 bytes (`align(64)` en L1).
- 🌡️ **El Físico:** Referencias de diseño de termodinámica de la información. Las cotas teóricas y los contadores de software no sustituyen mediciones de energía o rendimiento.
- 🩺 **El Médico:** Perspectiva de diseño sobre la carga operativa. La documentación no acredita diagnóstico fisiológico ni prevención de burnout.
- 🎵 **El Músico:** Armonía y resonancia dinámica. Tratamiento de los flujos de eventos como una partitura temporal con balance espectral y control de saturación.
- ⚖️ **El Abogado:** Evaluación de evidencia técnica relacionada con el EU AI Act. SQLite WAL y el encadenamiento de hashes no certifican conformidad ni impiden que el propietario del archivo borre o sustituya la base de datos.
- 🏛️ **El Filósofo:** Epistemología popperiana radical. Distinción innegociable entre mapa y territorio; falsación continua en código y silicio. Lo que no es falsable se rechaza como ruido.

### 3. Reglas compartidas entre clientes
El repositorio distribuye reglas y herramientas para clientes compatibles. La configuración y capacidades reales de cada cliente determinan qué reglas y herramientas utiliza:
- **Fuente Canónica Única:** `.babylon60rules`.
- **Topología de 7 Enlaces Simbólicos:** `verify_active_topology.py` comprueba los enlaces del checkout; eso no certifica qué instrucciones ha cargado cada cliente.
- **Servidor MCP Nativo y Portable:** Exposición de herramientas del kernel y memoria Cortex vía stdio sin dependencias en la nube ni rutas absolutas.
- **Micro-Servidores Efímeros (MCP Bomba):** Capacidad de sintetizar herramientas de un solo uso en subprocesos aislados con autodestrucción inmediata (*Burn-After-Use*) y recibo criptográfico en el ledger BFT.

---

## Instalación y Configuración

### Prerrequisitos
- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip
- Rust ≥ 1.80 (para el crate del kernel)

### Configuración Inicial

```bash
git clone https://github.com/borjamoskv/BABYLON-60.git
cd BABYLON-60

# Ejecutar la secuencia maestra de unboxing
python3 scripts/c5_setup/unboxing_moskv1.py

# O arrancar directamente el kernel nativo
cargo run --bin babylon60_kernel -- unbox
```

---

## Inicio Rápido

### Demo Asesino en 60 Segundos: Causal Gating & Apoptosis Fail-Stop

Este ejemplo ejercita un flujo de autorizaciones y evidencia. Revise su salida y los límites de las pruebas antes de atribuirle atestación biométrica hardware, confinamiento de otro proceso o cobertura de todos los efectos:

```bash
python3 scripts/c5_demos/c5_killer_demo_60s.py
```

### Estado de claims y evidencia (`CLAIMS.toml`)

`babylon.toml` y `RELEASE_MANIFEST.json` declaran v5.0.0 como `candidate`. El manifiesto registra 10 claims `verified` y 14 `empirical_and_bounded` (24 en total), asociados al commit que figura en él. No son 24 claims verificados ni una atestación de commits posteriores o cambios locales.

Para regenerar la evidencia de una candidata después de ejecutar los gates de release:

```bash
python3 scripts/c5_quality_gates/compile_claims_manifest.py --fresh
```

### Ejecutar la Demo Principal

Demuestra redacción de PII, verificación de frontera de serialización, fallback ante fallo de red y generación de artefactos técnicos de evidencia:

```bash
PYTHONPATH=. python3 scripts/c5_demos/run_hero_demo.py
```

### Añadir un Evento al Ledger (API Python)

```python
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent

ledger = CortexPersistLedger("$BABYLON_HOME/dbs/mi_agente_ledger.db")

event = CortexEvent(
    event_type="AGENT_ACTION",
    payload={"action": "search", "query": "ingresos trimestrales"},
    cortex_taint="session:abc123",
)

result = ledger.append_event(event)
# => {"seq": 1, "event_id": "...", "entry_hash": "...", "status": "C5_PERMANENT"}

# Verificar la cadena completa de hashes
assert ledger.verify_integrity()

# Obtener una raíz Merkle para atestación
root = ledger.get_merkle_root()
```

### Verificar Atestación del Ledger (CLI)

```bash
# Verificar un payload de atestación LLM
uv run babylon60-attest --file attestation_payload.json

# Generar Informe de Evidencias Técnicas para apoyar la Evaluación de Conformidad (EU AI Act)
# --ledger vincula el informe a evidencia real: el exportador re-ejecuta
# la verificación completa de la cadena de hashes y la comparación de la raíz
# Merkle antes de generar el expediente final, y lo firma con Ed25519.
uv run babylon60-compliance --bundle artifact_bundle_v3 \
    --ledger "$BABYLON_HOME/dbs/mi_agente_ledger.db" \
    --locale es --format html --output compliance_report.html

# Gestionar Licencias Enterprise
uv run babylon60-license generate --owner "AcmeCorp" --tier enterprise --days 365
uv run babylon60-license verify --key "AcmeCorp:enterprise:..."
```

---

## Configuración

### Variables de Entorno

| Variable | Requerida | Descripción |
| :--- | :--- | :--- |
| `BABYLON_HOME` | **Sí** | Directorio raíz para todas las bases de datos y estado. No tiene valor por defecto — debe establecerse explícitamente. |
| `GEMINI_HOME` | Solo scripts | Usado por scripts de exergía para rutas de vault/brain. |
| `BABYLON60_LICENSE_KEY` | Enterprise | Clave criptográfica de licencia para uso comercial (fallback: `BABYLON60_LICENSE_KEY`). |
| `BABYLON60_LICENSE_SALT` | Enterprise | Salt secreto HMAC para verificación de licencias. |
| `BABYLON60_SIGNING_SEED` | Evidence | Semilla Ed25519 de 64 caracteres hex para firmar informes de evidencia. Ausente o inválida: la firma se rechaza por defecto. |
| `BABYLON60_ALLOW_EPHEMERAL_SIGNING` | Solo evaluación | El valor `1` permite una clave efímera si falta la semilla; no establece una identidad persistente de confianza. |

### Ubicación de Datos

Todo el estado persistente se almacena bajo `$BABYLON_HOME/`:

```
$BABYLON_HOME/
├── dbs/                    # Bases de datos SQLite (ledger, memoria, etc.)
├── .babylon60/             # Ledger del agente de exergía
└── ...
```

---

## Verificación y Auditoría

### Verificación Programática de Integridad

```python
ledger = CortexPersistLedger("$BABYLON_HOME/dbs/mi_ledger.db")

# Verificación completa de la cadena de hashes
is_valid = ledger.verify_integrity()

# Manifiesto de atestación del estado
attestation = ledger.get_state_attestation()
# => {"total_entries": N, "merkle_root": "...", "integrity_verified": True, ...}
```

### Verificación Estática

```bash
# Lint + type check
make check

# O individualmente:
ruff check 01_ORCHESTRATOR/babylon60 tests
mypy 01_ORCHESTRATOR/babylon60 tests --strict --ignore-missing-imports
```

---

## Testing

```bash
# Suite de tests Python (ver CI para el recuento actual)
export BABYLON_HOME=/tmp/babylon
uv run pytest tests/ -v

# Tests del workspace Rust
cargo test --workspace

# Check CI completo (format + lint + typecheck + test)
make all
```

---

## Layout del Proyecto

```
BABYLON-60/
├── src/                          # Crate raíz Rust (SharedManifest, seqlock, halt)
├── 00_00_ABZU_KERNEL/            # Defensa y Verificación
│   ├── crates/                   #   Motores de ejecución #![no_std], circuitos ZK
│   └── formal_verification/      #   Proof IR → emisor Lean 4
├── 01_CORTEX_ENGINE/             # Sustrato de Memoria Cognitiva
│   ├── crates/                   #   Ejecutor runtime, puente nativo
│   └── transducers/              #   Transductores de procesamiento de datos
├── 01_ORCHESTRATOR/              # Núcleo Python
│   ├── babylon60/                #   Paquete Python core
│   │   ├── bft/                  #     Ledger con cadena de hashes (CortexPersistLedger)
│   │   ├── crypto/               #     Registro de hashes, AES, Ed25519, RFC 3161
│   │   ├── database/             #     Conector SQLite/WAL centralizado
│   │   ├── guards/               #     Validación URL/rutas/licencias
│   │   ├── attestation/          #     Anclaje Merkle DAG
│   │   ├── compliance_exporter/  #     Generador de informes técnicos para evaluación
│   │   └── cli/                  #     Puntos de entrada CLI
│   ├── cortex/                   #   Sustrato de memoria cognitiva Cortex (Python)
│   └── services/                 #   Servicios core
├── 02_AGENTS_ARCHI/              # Agentes Python
│   └── agents_archi/             #   Configuración y herramientas de agentes
├── proof/                        # Esbozo axiomático Lean 4 (lake build)
├── scripts/                      # Herramientas CLI, demos, verificadores
├── tests/                        # Suites de tests Python + Rust
├── docs/                         # Especificaciones, whitepapers, guías
└── tools/                        # Herramientas de atestación
```

---

## Repositorio Relacionado

- **[Teorema-Robinson-Moskv](https://github.com/borjamoskv/Teorema-Robinson-Moskv)** *(Enclave de Investigación Privado)*: Formalización matemática fundacional en Lean 4 de la que derivan los axiomas causales de BABYLON-60. *(Para verificación académica, los bocetos formales y la configuración de Lake están embebidos directamente en este monorepo en [`proof/`](../proof/)).*

---

## Limitaciones Conocidas

1. **Tamper-evident, no tamper-proof.** La cadena de hashes detecta modificaciones pero no puede prevenir que un atacante con acceso directo al filesystem reescriba la base de datos.
2. **Alcance BFT: Quórum Multi-Agente Intra-Host, No Consenso WAN Distribuido.** La capa BFT exige quórums criptográficos de $(2f + 1)$ firmas Ed25519 entre enjambres locales de agentes (`consensus_validator.py`) y memoria compartida zero-copy (`iceoryx2`). El consenso está acotado deliberadamente a procesos locales; la replicación multi-máquina delega en persistencia single-writer con testigos externos Git/SCITT, no en consenso bizantino por red.
3. **Deuda técnica `except Exception`.** Varios módulos en `01_ORCHESTRATOR/babylon60/` y `scripts/` usan manejadores de excepciones amplios. Están rastreados y se estrechan incrementalmente.
4. **`sqlite3.connect` directo en scripts.** Algunos scripts evitan el conector centralizado `01_KISH_ENGINE/babylon60/database/core.py`. La migración está en progreso.
5. **`BABYLON_HOME` requerido.** El sistema no arrancará sin esta variable de entorno — los fallbacks `Path.home()` han sido eliminados por política.
6. **Coexisten dos implementaciones de ledger.** El `CortexPersistLedger` síncrono (quick-start) y el `BFTLedgerActor` asíncrono (usado por los tests de resiliencia) comparten semántica pero no código. Su consolidación está rastreada como trabajo futuro.

---

## Licencia

**Licencia Dual Soberana v4.0:**

| Tier | Acceso | Requisito |
| :--- | :--- | :--- |
| **Soberano** | Individuos, investigadores, uso no-comercial | Gratis — 100% Open Core |
| **Enterprise** | Corporaciones, uso comercial, producción | `BABYLON60_LICENSE_KEY` criptográfica |

Ver [LICENSE](../LICENSE) y [COMMERCIAL_LICENSE.md](./COMMERCIAL_LICENSE.md).

---

## Seguridad

Reportar vulnerabilidades a **security@babylon60.com** — no usar GitHub Issues públicos.  
SLA: acuse de recibo < 24h, remediación < 72h.  
Ver [SECURITY.md](../SECURITY.md).

---

<sub>BABYLON-60 v5.0.0 · Ledger Criptográfico Tamper-Evident para Agentes IA · Borja Moskv</sub>
