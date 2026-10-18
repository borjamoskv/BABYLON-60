# ADR-002: Puente FFI PyO3/Maturin para Runtime Híbrido Rust-Python

![Status: C5-REAL](https://img.shields.io/badge/Status-C5--REAL-black?style=flat-square&logo=rust&logoColor=white)


- **Estado:** Aceptada
- **Fecha:** 2026-08-06
- **Autor:** Borja Moskv (borjamoskv)

## Contexto

BABYLON-60 opera como un sistema híbrido con:
- **Rust:** Kernel de ejecución, criptografía, consenso BFT, compilador IR (12.8K LOC en 7 crates).
- **Python:** SDK de alto nivel, CLI, compliance exporter, transducers, cortex engine (80K LOC en 24 paquetes).

Se necesita un puente FFI (Foreign Function Interface) para exponer las funciones Rust de alto rendimiento al runtime Python sin sacrificar seguridad de memoria.

## Decisión

Se selecciona **PyO3 + Maturin** como stack de FFI.

## Justificación

### Alternativas evaluadas

| Alternativa | Pros | Contras |
|---|---|---|
| **PyO3 + Maturin** | Zero-copy, GIL management, build system integrado, wheels PEP 517 | Acoplamiento al ABI de CPython |
| **cffi + C headers** | Máxima portabilidad | Requiere capa C intermedia, pérdida de tipos Rust |
| **pyo3-asyncio** | Soporte async nativo | Complejidad de event loop cruzado |
| **WASM + wasmtime** | Sandbox total | Overhead de serialización, no accede a hardware |

### Razones clave

1. **Build determinista:** Maturin genera wheels PEP 517 directamente desde `Cargo.toml` + `pyproject.toml`, eliminando la necesidad de scripts de build ad-hoc. El `pyproject.toml` del proyecto ya declara `build-backend = "maturin"`.

2. **Seguridad de tipos:** PyO3 mapea tipos Rust (structs, enums, Result) directamente a tipos Python (clases, excepciones), preservando las invariantes de tipos a través de la frontera FFI.

3. **GIL release controlado:** Las operaciones computacionalmente intensivas (hash criptográfico, verificación de ledger) liberan el GIL explícitamente, permitiendo concurrencia real en el lado Python.

4. **Ecosistema maduro:** PyO3 es el estándar de facto para Rust-Python FFI con >3K estrellas GitHub, adoptado por Polars, Pydantic v2, y cryptography.

## Consecuencias

- **Positivas:** Build reproducible con un solo comando (`maturin develop`). Wheels publicables a PyPI sin infraestructura adicional. Tests Python pueden ejercitar código Rust directamente.
- **Negativas:** Acoplamiento a CPython (no compatible con PyPy ni GraalPy). Compilación cruzada requiere configuración de targets en `.cargo/config.toml`.
- **Riesgo:** Actualizaciones de ABI de CPython (3.12 → 3.13) pueden requerir rebuild. Mitigación: CI multiplatform con matriz de versiones Python.

## Referencias

- PyO3: https://pyo3.rs
- Maturin: https://www.maturin.rs
- PEP 517: https://peps.python.org/pep-0517/
