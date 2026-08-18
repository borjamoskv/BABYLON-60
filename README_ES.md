# BABYLON-60

[🌐 Read in English](README.md)

**Ledger criptográfico local, a prueba de manipulaciones, para agentes de IA autónomos.**

[![Version](https://img.shields.io/badge/version-4.0.0-black?style=flat-square)](https://github.com/borjamoskv/BABYLON-60)
[![License](https://img.shields.io/badge/license-Sovereign_Dual--License-orange?style=flat-square)](./LICENSE)
[![Python](https://img.shields.io/badge/python-≥3.10-blue?style=flat-square)](./pyproject.toml)
[![Rust](https://img.shields.io/badge/rust-≥1.77-orange?style=flat-square)](./Cargo.toml)

---

## Qué es BABYLON-60

BABYLON-60 es un monorepo que proporciona un **ledger append-only con cadena de hashes** respaldado por SQLite WAL y un kernel Rust de IPC de bajo nivel. Está diseñado para que los agentes de IA — independientemente del LLM u orquestador que los dirija — produzcan un rastro auditable y a prueba de manipulaciones de cada acción que realizan.

**Idea central:** cada evento que un agente produce se añade a una base de datos SQLite local con una cadena de hashes SHA3-256. El hash de cada entrada cubre el hash de la entrada anterior, creando una secuencia enlazada donde cualquier modificación retroactiva rompe la cadena y es detectable programáticamente.

### Qué Es

- Una capa de persistencia **local-first**: todos los datos permanecen en tu máquina en `$BABYLON_HOME/`.
- Un ledger **tamper-evident** (detectable, no a prueba de manipulación) con verificación de integridad por cadena de hashes.
- Una base de datos **single-writer SQLite/WAL** con `busy_timeout=5000ms`, `synchronous=FULL` y `foreign_keys=ON`.
- Un kernel Rust que proporciona un slot IPC lock-free de 64 bytes (`SharedManifest`) con semántica fail-stop y recibos COSE_Sign1.
- Un exportador de cumplimiento que genera certificados listos para auditoría para autoridades supervisoras del EU AI Act (AESIA, BSI, CNIL).

### Qué No Es

- No es un sistema de consenso distribuido (sin quórum BFT/PBFT en vivo). El consenso se logra *a posteriori* mediante testigos externos Git Sentinel.
- No es a prueba de manipulación contra un atacante con acceso al filesystem que evite el motor de base de datos.
- No es un reemplazo para tu LLM o framework de agentes — se envuelve alrededor de ellos como capa de rendición de cuentas.

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│   Tu Stack de Agentes (LangChain / AutoGen / CrewAI / Ollama)│
├──────────────────────────────────────────────────────────────┤
│   BABYLON-60 Capa de Rendición de Cuentas                    │
│                                                              │
│   Python (packages/babylon60/)                               │
│   ├── bft/          Ledger con cadena de hashes (SHA3-256)   │
│   ├── crypto/       Registro de hashes, AES-256-GCM, Ed25519│
│   ├── database/     Conector SQLite/WAL single-writer        │
│   ├── guards/       Validación URL, rutas, licencias         │
│   ├── attestation/  Anclaje Merkle DAG                       │
│   └── compliance_exporter/  Certificados EU AI Act           │
│                                                              │
│   Rust (src/ + crates/)                                      │
│   ├── SharedManifest    64 B IPC lock-free (AArch64/x86)     │
│   ├── seqlock           Lectores SPMC, zero RFO              │
│   ├── halt              Fail-stop + recibos COSE_Sign1       │
│   └── thermodynamics    Bisimulación suelo de Landauer       │
├──────────────────────────────────────────────────────────────┤
│   Base de Datos SQLite WAL ($BABYLON_HOME/dbs/)              │
└──────────────────────────────────────────────────────────────┘
```

---

## Propiedades de Seguridad e Integridad

| Propiedad | Mecanismo | Limitación |
| :--- | :--- | :--- |
| **Cadena de hashes** | Cada entrada del ledger incluye un hash SHA3-256 de la entrada anterior. `verify_integrity()` recomputa y valida la cadena completa. | Detecta manipulación *a posteriori*; no la previene si el atacante evita SQLite. |
| **Append-only** | Triggers SQLite (`trg_ledger_immutable_update` / `trg_ledger_immutable_delete`) bloquean UPDATE/DELETE a nivel de motor. | Evitable mediante manipulación directa del filesystem fuera del motor DB. |
| **Single-writer WAL** | Todas las conexiones del paquete core y scripts del repositorio usan `PRAGMA journal_mode=WAL` + `busy_timeout=5000` via el conector centralizado en [`database/core.py`](./packages/babylon60/database/core.py). | Migración 100% completada en todo el árbol de código. |
| **Idempotencia** | Claves UUID v5 por evento previenen inserción duplicada. | Alcance limitado a una instancia de ledger. |
| **Ordenamiento Lamport** | Timestamps Lamport monótonamente crecientes imponen orden causal. | Reloj lógico, no wall-clock; sin coordinación distribuida. |
| **Testigo externo** | Git Sentinel inyecta `Ledger-Head` y `Ledger-Seq` como trailers de commit. Los runners CI actúan como testigos independientes. | Requiere push a remoto; sin protección durante operación solo-offline. |
| **Agilidad criptográfica** | [`hash_registry.py`](./packages/babylon60/crypto/hash_registry.py) permite cambiar algoritmos hash (SHA-256, SHA3-256, SHA-512, SHA3-512) al inicio. | Cambiar algoritmo a mitad de sesión rompe la cadena de hashes (por diseño). |

---

## Instalación

### Prerrequisitos

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/) (recomendado) o pip
- Rust ≥ 1.77 (para el crate del kernel)

### Configuración

```bash
git clone https://github.com/borjamoskv/BABYLON-60.git
cd BABYLON-60

# Establecer la variable de entorno requerida
export BABYLON_HOME="$HOME/.babylon60"
mkdir -p "$BABYLON_HOME"

# Instalar dependencias Python
uv sync

# Compilar y testear el workspace Rust
cargo test --workspace
```

---

## Inicio Rápido

### Ejecutar la Demo

Demuestra redacción de PII, verificación de frontera de serialización, fallback ante fallo de red y generación de certificados de cumplimiento:

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

result = ledger.append(event)
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

# Generar Certificado de Cumplimiento EU AI Act (JSON / Markdown / HTML)
uv run babylon60-compliance --bundle artifact_bundle_v3 --locale es --format html --output cert.html

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
| `BABYLON60_LICENSE_KEY` | Enterprise | Clave criptográfica de licencia para uso comercial (fallback: `CORTEX_LICENSE_KEY`). |
| `BABYLON60_LICENSE_SALT` | Enterprise | Salt secreto HMAC para verificación de licencias. |

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
ruff check packages/babylon60 tests
mypy packages/babylon60 tests --strict --ignore-missing-imports
```

---

## Testing

```bash
# Suite de tests Python (377 tests)
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
├── crates/
│   ├── babylon60-kernel/         # Motor de ejecución #![no_std]
│   ├── babylon60-compiler/       # Lexer/parser DSL .b60
│   ├── babylon60-proof-ir/       # Proof IR → emisor Lean 4
│   ├── babylon60-runtime/        # Ejecutor runtime
│   ├── strike-rs/                # Puente nativo PyO3, taint BLAKE3
│   └── nul-zk/                   # Compilación de circuitos ZK
├── packages/
│   ├── babylon60/                # Paquete Python core
│   │   ├── bft/                  # Ledger con cadena de hashes (CortexPersistLedger)
│   │   ├── crypto/               # Registro de hashes, AES, Ed25519, RFC 3161
│   │   ├── database/             # Conector SQLite/WAL centralizado
│   │   ├── guards/               # Validación URL/rutas/licencias
│   │   ├── attestation/          # Anclaje Merkle DAG
│   │   ├── compliance_exporter/  # Generador certificados EU AI Act
│   │   ├── cli/                  # Puntos de entrada CLI
│   │   ├── primitives/           # Aritmética F60, tipos result, serialización
│   │   └── transducers/          # Cache, higiene, procesamiento de datos
│   └── cortex/                   # Sustrato de memoria cognitiva Cortex
├── apps/
│   ├── babylon60-ide/            # IDE desktop Tauri v2
│   ├── web/                      # UI de telemetría React
│   └── tonnetz_app/              # Visualizador armónico Neo-Riemanniano
├── scripts/                      # Herramientas CLI, demos, verificadores
├── tests/                        # Suites de tests Python + Rust
├── docs/                         # Especificaciones, whitepapers, guías
├── experiments/                  # Prototipos de investigación
└── tools/                        # Herramientas de atestación
```

---

## Repositorio Relacionado

- **[Teorema-Robinson-Moskv](https://github.com/borjamoskv/Teorema-Robinson-Moskv)**: Formalización matemática fundacional en Lean 4 de la que derivan los axiomas causales de BABYLON-60.

---

## Limitaciones Conocidas

1. **Tamper-evident, no tamper-proof.** La cadena de hashes detecta modificaciones pero no puede prevenir que un atacante con acceso directo al filesystem reescriba la base de datos.
2. **Sin consenso distribuido en vivo.** El nombre del módulo BFT es aspiracional; la arquitectura actual usa persistencia local single-writer con testigos Git externos (Escalón 3). BFT en vivo (Escalón 4) es un objetivo futuro.
3. **Deuda técnica `except Exception`.** Módulos core de `packages/babylon60/` refactorizados a excepciones explícitas; scripts secundarios en estrechamiento incremental.
4. **`sqlite3.connect` directo erradicado.** Todos los módulos y scripts usan el conector centralizado `database/core.py` (migración 100% completada).
5. **`BABYLON_HOME` requerido.** El sistema no arrancará sin esta variable de entorno — los fallbacks `Path.home()` han sido eliminados por política.

---

## Licencia

**Licencia Dual Soberana v4.0:**

| Tier | Acceso | Requisito |
| :--- | :--- | :--- |
| **Soberano** | Individuos, investigadores, uso no-comercial | Gratis — 100% Open Core |
| **Enterprise** | Corporaciones, uso comercial, producción | `CORTEX_LICENSE_KEY` criptográfica |

Ver [LICENSE](./LICENSE) y [COMMERCIAL_LICENSE.md](./docs/COMMERCIAL_LICENSE.md).

---

## Seguridad

Reportar vulnerabilidades a **security@babylon60.com** — no usar GitHub Issues públicos.  
SLA: acuse de recibo < 24h, remediación < 72h.  
Ver [SECURITY.md](./SECURITY.md).

---

<sub>BABYLON-60 v4.0.0 · Ledger Criptográfico Tamper-Evident para Agentes IA · Borja Moskv</sub>
