# 🧪 TESTS — Suites de Verificación Empírica, Mediación `INV-Ω` y Falsación (`tests/`)

> **CAPA DE DEMOSTRACIÓN EMPÍRICA Y PRUEBAS ADVERSARIALES (`L2`–`L4`)**  
> Ubicación: `tests/`  
> Agrupa las suites de pruebas en Python (`pytest`) y los tests de integración y campañas adversariales en Rust (`cargo test`) que respaldan las declaraciones de [`CLAIMS.toml`](../CLAIMS.toml).

---

## 📐 Estructura de `tests/`

```
tests/
├── conftest.py                  # Configuración Pytest y fixtures de aislamiento
├── babylon60/                   # Pruebas unitarias específicas del paquete babylon60
├── conformance/                 # Pruebas de conformidad formal y esquemas
├── differential/                # Pruebas de ejecución diferencial (Rust vs Python)
├── fixtures/                    # Datos y estados de prueba deterministas
├── fuzz/                        # Tests de fuzzing para detectores y parsers
├── licensing/                   # Validación de paridad y restricciones de licencia
├── property/                    # Pruebas basadas en propiedades (Hypothesis)
├── replay/                      # Reconstrucción y rechazo de replay en ledger
├── spsc_miri_probe/             # Sonda aislada de memoria para colas SPSC bajo Miri
├── test_*.py                    # Suites de pruebas Python (seguridad, MCP, BFT, release, M0)
├── *.rs                         # Campañas de integración y estrés en Rust (INV-OMEGA, NEMESIS, ACS)
└── *.cpp                        # Micro-benchmarks de referencia en C++
```

---

## 🔍 Taxonomía de las Suites Principales

### 1. Campañas de Mediación Completa y Seguridad en Rust (`CLAIMS.toml`)
* **[`omega_mediation_campaign.rs`](omega_mediation_campaign.rs)**: Campaña reproducible de 5 pruebas (`BYPASS-001` a `REVOCATION-005`) y corte de grafo `NEMESIS` bajo confinamiento macOS Seatbelt (`[claim.INV_OMEGA_complete_mediation]`).
* **[`adversarial_nemesis.rs`](adversarial_nemesis.rs)**, **[`nemesis_wave3.rs`](nemesis_wave3.rs)** & **[`nemesis_wave4.rs`](nemesis_wave4.rs)**: Pruebas adversariales de carrera TOCTOU en `DELETE_FILE` (`AUTH_004`, `AUTH_007`), pérdida de recibo tras `SIGKILL` (`FL_014`) y deriva de políticas (`FL_016`).
* **[`admission_capability_test.rs`](admission_capability_test.rs)** & **[`acs_authenticated.rs`](acs_authenticated.rs)**: Control de admisión acotado (`FL_007`), broker de capacidades acotadas (`FL_008`) y guardia OWASP ACS v0.1.0 (`FL_016`).
* **[`seqlock_loom.rs`](seqlock_loom.rs)**: Model checking acotado en Loom del protocolo Seqlock SPMC (`inv_02_seqlock_concurrency`).

### 2. Evidencia de Release, Paquete M0 y Distribución Terminal (Python)
* **[`test_audit_public_claims.py`](test_audit_public_claims.py)**, **[`test_release_evidence.py`](test_release_evidence.py)** & **[`test_release_verification.py`](test_release_verification.py)**: Verificación de contratos de [`CLAIMS.toml`](../CLAIMS.toml), matriz normativa de hashes (`BLAKE3` / `SHA-256` / `SHA3-256`), cotas `SIGKILL` vs. corte eléctrico y validación de SBOM/manifiestos.
* **[`test_m0_evidence_pack_acceptance.py`](test_m0_evidence_pack_acceptance.py)**: Compilación determinista y verificación criptográfica independiente del paquete `babylon-m0-evidence-pack/`.
* **[`test_terminal_distribution.py`](test_terminal_distribution.py)**: Empaquetado limpio, instaladores (`install.sh` / `install.ps1`) y validación de enlaces de gobernanza.

### 3. Aislamiento MCP, Ledger BFT y Enjambres
* **[`test_ax0_mcp_isolation.py`](test_ax0_mcp_isolation.py)**, **[`test_mcp_seatbelt.py`](test_mcp_seatbelt.py)** & **[`test_mcp_deduction.py`](test_mcp_deduction.py)**: Cumplimiento de `AX-0` y confinamiento Seatbelt de servidores MCP.
* **[`test_ledger_resilience.py`](test_ledger_resilience.py)**, **[`test_master_ledger_queue.py`](test_master_ledger_queue.py)** & **[`test_bittensor_yuma_consensus.py`](test_bittensor_yuma_consensus.py)**: Persistencia transaccional SQLite WAL, encadenamiento de hashes y pruebas de consenso.
* **[`test_swarm_100_concurrency.py`](test_swarm_100_concurrency.py)** & **[`test_agents_archi.py`](test_agents_archi.py)**: Contención de 100 workers concurrentes (`[claim.sharur_100_swarm_concurrency]`).

### 4. Invariantes C5-REAL y Aritmética Base-60
* **[`test_c5_invariants.py`](test_c5_invariants.py)**, **[`test_axioms_hypothesis.py`](test_axioms_hypothesis.py)** & **[`test_inv_c5_28_falsification.py`](test_inv_c5_28_falsification.py)**: Pruebas basadas en propiedades con Hypothesis.
* **[`test_base60.py`](test_base60.py)** & **[`test_f60_arithmetic.py`](test_f60_arithmetic.py)**: Operaciones aritméticas sexagesimales exactas.

---

## 🛠️ Comandos de Ejecución

```bash
# Ejecutar una suite Python dirigida (pyproject.toml configura pythonpath automáticamente)
uv run --locked pytest tests/test_audit_public_claims.py tests/test_m0_evidence_pack_acceptance.py -q

# Ejecutar todas las pruebas unitarias de Rust
cargo test --locked --lib

# Listar o verificar todos los claims declarados en CLAIMS.toml
python3 scripts/c5_quality_gates/verify_claims.py --list
```
