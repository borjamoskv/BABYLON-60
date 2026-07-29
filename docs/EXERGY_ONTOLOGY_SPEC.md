# Exergy-Optimized Ontology, Naming, and Semantics Specification

Este documento establece las reglas mecánicas para estructurar nombres, tipologías y semánticas de código y datos con el objetivo técnico de **minimizar el consumo de tokens (BPE), reducir fallos de caché/atención en LLMs y maximizar la velocidad de compilación y verificación estática ($O(1)$ / $O(\log N)$)**.

---

## 1. Naming Structure (Alineación con Tokenizadores BPE y AST)

El objetivo físico del nombrado no es la estética literaria, sino la **compresión algorítmica** y el **enrutamiento rápido de punteros en AST / caché de atención**.

### A. Minimización de Fragmentación de Tokens (BPE Alignment)
Los tokenizadores (como `cl100k_base` o los de Llama/Mamba) fragmentan identificadores largos en múltiples tokens sin significado independiente, diluyendo el peso de atención del modelo.

* **Regla**: Preferir `snake_case` con primitivas semánticas consolidadas en lugar de `camelCase` excesivamente verboso.
  * ❌ *Entrópico (6 tokens)*: `calculateTotalRevenueFromUserTransactions`
  * ✅ *Exergético (3 tokens)*: `calc_user_revenue_usd`
* **Regla**: Mantener los identificadores por debajo de **24 caracteres** para encajar en registros de caché cortos y líneas de inspección sin saltos visuales en buffers del IDE.

### B. Prefijado por Dominio de Aislamiento (Namespace Indexing)
Permite la búsqueda e indexación en $O(1)$ utilizando herramientas binarias (`ripgrep`, `grep_search`, `ctags`) sin necesidad de construir el grafo completo de dependencias.

| Prefijo | Dominio de Memoria/AST | Ejemplo |
| :--- | :--- | :--- |
| `core_` | Primitivas puras (sin I/O, sin estado global) | `core_matrix_mul` |
| `io_` | Operaciones de disco, red o transductores de hardware | `io_read_wal_chunk` |
| `mut_` | Funciones impuras que modifican estado o referencias | `mut_append_ledger` |
| `cfg_` | Estructuras inmutables de configuración o constantes | `cfg_max_timeout_ms` |
| `test_` | Aserciones empíricas y falsación unitaria | `test_ssm_invariants` |

---

## 2. Ontology (Topología del Grafo de Conocimiento y Tipos)

Una ontología eficiente elimina las dependencias implícitas, la herencia profunda y los bucles circulares, imponiendo una topología de **Grafo Acíclico Dirigido (DAG)** o **Conjunto Parcialmente Ordenado (Poset)**.

### A. Tipado Estructural Estricto (No-Any, Strict Schemas)
* **Regla**: Toda entidad debe tener un contrato explícito de **Entrada**, **Salida** y **Modo de Fallo**. Queda prohibido el uso de tipos genéricos (`Any`, `object`, `dict` sin tipar) que obligan al runtime o al LLM a inferir campos dinámicamente en tiempo de ejecución.
* **Implementación (Python)**: Uso exclusivo de `dataclasses`, `Pydantic v2` (con validación en Rust) o `TypedDict` estrictos, validados en CI por `mypy --strict`.

### B. Indexación por Hash (Content-Addressable Storage)
* **Regla**: Las referencias entre nodos del sistema o artefactos no deben depender de rutas relativas frágiles (`../../data/info.json`) ni de descripciones textuales vagas ("el script de cálculo").
* **Mecanismo**: Referenciar siempre por **Hash SHA256 / Git Commit ID** o por **Nombre Cualificado Absoluto (`pkg.module.Symbol`)**. Esto garantiza que la validación de integridad sea matemática y determinista.

---

## 3. Semantics (Gramática Causal y Determinismo)

La semántica define cómo las operaciones alteran el estado del sistema. Para maximizar la exergía, debe ser inequívoca, local y verificable.

### A. Gramática Imperativa y Causal en Contratos
* **Regla**: Los comentarios de documentación (`docstrings`) y contratos de sistema deben eliminar la prosa pasiva o descriptiva. Deben redactarse en formato de **Transición de Estado (`Precondición -> Operación -> Postcondición`)**.
  * ❌ *Pasiva*: "Esta función revisa si el usuario tiene saldo y luego actualiza la base de datos."
  * ✅ *Causal*: `Pre: user_id en DB -> Exec: tx_deduct(balance) -> Post: ledger_hash actualizado || raise InsufficientFunds`

### B. Isomorfismo Intención-Ejecución (Zero Magic)
* **Regla**: No debe existir disparidad entre el nombre de un símbolo y su efecto termodinámico en el hardware. Si una función se llama `get_user()`, es **estrictamente de solo lectura (`pure/idempotent`)**. Si realiza llamadas a red o escrituras en caché, debe llamarse `io_fetch_user_cached()`.

### C. Falsabilidad Inmediata (Fail-Fast Boundary)
* **Regla**: Toda violación de precondición semántica debe provocar el colapso inmediato de la ejecución (`raise ValueError`, `assert`, o `exit(1)`). Queda prohibido enmascarar errores con valores por defecto silenciosos (`return None`, `return ""` o bloques `try/except: pass`), ya que propagan datos corruptos consumiendo ciclos de cómputo inútiles aguas abajo.
