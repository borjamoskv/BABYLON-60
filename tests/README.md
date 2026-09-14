# 🧪 TESTS — Suite Multimodal de Verificación & Falsación Popperiana

> **CAPA DE DEMOSTRACIÓN EMPÍRICA Y PRUEBAS DE ESTRÉS**  
> Ubicación: `tests/`  
> Agrupa los 417 test cases de la suite `pytest`, harnesses en Rust (con `loom` y `property_test`), benchmarks en C++ y suites de fuzzing/diferenciales de **BABYLON-60**.

---

## 📐 Estructura de la Suite de Pruebas

```
tests/
├── conftest.py                  # Configuración Pytest y fixtures globales de aislamiento
├── babylon60/                   # Pruebas unitarias específicas del paquete babylon60
├── conformance/                 # Pruebas de conformidad formal y estándares
├── differential/                # Pruebas de ejecución diferencial (Rust vs Python)
├── fixtures/                    # Datos y estados de prueba deterministas
├── fuzz/                        # Tests de fuzzing entrópico para detectores de alucinación
├── property/                    # Pruebas de propiedad basándose en hipótesis (Hypothesis)
├── replay/                      # Reconstrucción y replay de logs de ledger
├── test_*.py                    # 46 suites de pruebas unitarias e integración Python (417 test cases)
├── *_test.rs & unit_tests.rs   # Harnesses y suites de pruebas en Rust nativo
└── *.cpp                        # Benchmarks en C++ (cinética de caché & SPSC ringbuffer)
```

---

## 🔍 Taxonomía de las Suites Principales

### 1. Invariantes C5-REAL & Falsación Popperiana
* **[`test_c5_invariants.py`](test_c5_invariants.py)** & **[`test_axioms_hypothesis.py`](test_axioms_hypothesis.py)**: Validación de invariantes de alta exergía y pruebas basadas en propiedades con Hypothesis.
* **[`test_inv_c5_28_falsification.py`](test_inv_c5_28_falsification.py)**: Test de falsación de proposiciones en tiempo de ejecución.

### 2. Consenso BFT & Resiliencia de Ledger
* **[`test_hotstuff_consensus.py`](test_hotstuff_consensus.py)**, **[`test_raft_consensus.py`](test_raft_consensus.py)** & **[`test_bittensor_yuma_consensus.py`](test_bittensor_yuma_consensus.py)**: Simulación de algoritmos de consenso tolerantes a fallos bizantinos.
* **[`test_ledger_resilience.py`](test_ledger_resilience.py)** & **[`test_master_ledger_queue.py`](test_master_ledger_queue.py)**: Prueba de concurrencia y recuperación ante desastres.

### 3. Kernel Nativo & Inferencia Verificable
* **[`test_kernel_native_modules.py`](test_kernel_native_modules.py)**: Verificación del motor CDP de navegador, cliente Kimi y sincronización QuantumSync.
* **[`test_verifiable_inference.py`](test_verifiable_inference.py)** & **[`test_mcp_deduction.py`](test_mcp_deduction.py)**: Test de firmas criptográficas de inferencia y oráculos deductivos MCP.

### 4. Primitivas C5 & Aritmética Base-60
* **[`test_base60.py`](test_base60.py)** & **[`test_f60_arithmetic.py`](test_f60_arithmetic.py)**: Verificación de las operaciones aritméticas sexagesimales babilónicas.

---

## 🛠️ Comandos de Ejecución

```bash
# Ejecución completa de la suite Python (417 test cases)
PYTHONPATH=packages:. pytest tests/

# Ejecución de una suite específica
PYTHONPATH=packages:. pytest tests/test_kernel_native_modules.py

# Pruebas nativas de Rust
cargo test

# Pruebas con informe de cobertura
PYTHONPATH=packages:. pytest --cov=packages tests/
```
