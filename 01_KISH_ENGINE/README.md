# 🐍 01_KISH_ENGINE — Motor Cognitivo Python, CLI, Servidor MCP y Ledger BFT (`01_KISH_ENGINE/`)

> **DOMINIO ARQUITECTÓNICO: `01_KISH_ENGINE` (`kish.engine` — Anillo-1)**  
> Ubicación: `01_KISH_ENGINE/`  
> Contiene el paquete Python principal `babylon60`, la CLI de terminal (`babylon60`), el servidor de memoria y herramientas MCP (`babylon60-mcp`), el ledger BFT en SQLite WAL (`cortex_persist_sqlite`), el compilador de paquetes de evidencia (`compliance_exporter/`) y el verificador independiente (`verifier/`).

---

## 🏛️ Taxonomía de `01_KISH_ENGINE/`

```
01_KISH_ENGINE/
├── babylon60/                  # Paquete principal Python de BABYLON-60
│   ├── bft/                    # Ledger SQLite WAL (SHA3-256 legado), árboles Merkle y canales IPC BLAKE3
│   ├── cli/                    # Despachador CLI (`babylon60 doctor`, `setup`, `approve`, `presentation`)
│   ├── mcp/                    # Servidor MCP por stdio (`cortex_mcp_server.py`) y despacho de efectos
│   ├── compliance_exporter/    # Compilador determinista del paquete M0 (`m0_evidence_pack.py`, EU AI Act)
│   ├── verifier/               # Verificador independiente (`standalone_verify.py`, dual BLAKE3 / SHA3-256)
│   ├── cognitive_pilot/        # Evaluación reproducible de gobernanza y pilotos de sesión
│   ├── guards/                 # Guardias de capacidad, licencias y gate biométrico (`c5_biometric_gate.swift`)
│   ├── kernel/                 # Subsistemas de orquestación, deducción MCP, Seatbelt y firewall Z3
│   ├── transducers/            # Guardias de exergía de renderizado (`BLAKE3`), compresión y telemetría
│   ├── primitives/             # Primitivas Base-60 (`base60.py`), CBOR canónico y matrices de desintegración
│   ├── verification/           # Atestación de hardware, gradación AST y falsación Popperiana
│   └── verifiable_inference/   # Streamer Python para inferencia MoE (`edge0_moe_streamer.py`)
├── cortex/                     # Subsistema de almacenamiento contextual y crates auxiliares (`cortex-guard`)
├── extensions/                 # Extensiones modulares de sincronización
└── services/                   # Servicios auxiliares (`email_inbound/`)
```

---

## 🔍 Resumen por Subsistema Canónico

### 1. `01_KISH_ENGINE/babylon60/bft/` — Ledger Persistente & Árboles Merkle
* **[`README.md`](./babylon60/bft/README.md)**: Especificación de persistencia transaccional en SQLite WAL (`PRAGMA synchronous = FULL`, `BEGIN IMMEDIATE`).
* **`cortex_persist_ledger.py` & `consensus_ledger.py`**: Encadenamiento de hashes de filas en SQLite (`SHA3-256` legado, `[claim.cortex_persist_sqlite]`) y raíces Merkle deterministas (`[claim.merkle_attestation]`).
* **`exergy_binary_ipc.py` & `bounty_ring_dispatcher.py`**: Tramas IPC inter-agente autenticadas con `BLAKE3` (`INV_C5_ONWIRE_CANON`).

### 2. `01_KISH_ENGINE/babylon60/mcp/` & `cli/` — Distribución Terminal y Mediación MCP
* **`cortex_mcp_server.py` & `effect_dispatch.py`**: Servidor MCP por stdio con aislamiento `AX-0` (`[claim.mcp_authority_gate]`: clientes estocásticos no pueden auto-autorizar acciones protegidas) y digestos `BLAKE3` de integridad de módulos.
* **`main_dispatcher.py`**: Punto de entrada de la CLI `babylon60` (compatible con macOS, Linux y Windows Python 3.11/3.12).

### 3. `01_KISH_ENGINE/babylon60/compliance_exporter/` & `verifier/` — Evidencia Auditada (`M0`)
* **`m0_evidence_pack.py`**: Compila dinámicamente las declaraciones de [`CLAIMS.toml`](../CLAIMS.toml) en el paquete verificable `babylon-m0-evidence-pack/`, separando controles `BROKER_MEDIATED` de `OS_ENFORCED`.
* **`standalone_verify.py`**: Verificador autónomo que comprueba firmas Ed25519, cadenas SQLite, checksums `SHA-256` y raíces Merkle (`BLAKE3` canónico y `SHA3-256` legado).

### 4. `01_KISH_ENGINE/babylon60/kernel/` — Deducción MCP, Confinamiento Seatbelt y Z3
* **[`README.md`](./babylon60/kernel/README.md)**: Validación de protocolo stdio y confinamiento `sandbox-exec` en macOS (`[claim.mcp_seatbelt_confinement]`), scaffolding de servidores MCP efímeros (`mcp_scaffolder.py` con digest `BLAKE3`) y cortafuegos Z3 (`z3_firewall.py`).

### 5. `01_KISH_ENGINE/babylon60/guards/` & `verification/` — Salvaguardas y Atestación
* **`c5_biometric_gate.swift` & `hardware_attestation.py`**: Integración con Apple Secure Enclave (P-256) y Touch ID para efectos protegidos.
* **`capability_guard.py` & `contradiction_guard.py`**: Aislamiento por capacidades y detección de estados contradictorios.

---

## 🛠️ Comandos de Verificación

```bash
# Ejecutar pruebas del ledger, Merkle, aislamiento AX-0 y confinamiento MCP
uv run --locked pytest tests/ -k "test_ledger or test_merkle" -q
uv run --locked pytest tests/test_ax0_mcp_isolation.py tests/test_mcp_seatbelt.py -q

# Ejecutar pruebas de aceptación del paquete de evidencia M0
uv run --locked pytest tests/test_m0_evidence_pack_acceptance.py -q
```
