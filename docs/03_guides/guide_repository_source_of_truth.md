---
title: Fuentes de nombres, código y comprobaciones
status: Maintained reference
version: 5.0.0
---

# Fuentes de nombres, código y comprobaciones

Los manifiestos definen los nombres instalables. La documentación describe su
uso; un nombre histórico no crea un alias que el paquete no publica.

| Entidad | Nombre o ruta vigente | Fuente |
| --- | --- | --- |
| Distribución Python | `babylon60` | [pyproject.toml](../../pyproject.toml) |
| Namespace Python | `babylon60` bajo `01_KISH_ENGINE/` | [paquete](../../01_KISH_ENGINE/babylon60/) |
| CLI Python | `babylon60` | `[project.scripts]` de `pyproject.toml` |
| Exportador | `babylon60-compliance` | `[project.scripts]` de `pyproject.toml` |
| Paquete Cargo raíz | `babylon60_root` | [Cargo.toml](../../Cargo.toml) |
| Intérprete DSL Rust | target Cargo `babylon60`, fuente `src/babylon60.rs` | [tutorial](tutorial_hello_causal.md) |
| CLI del kernel Rust | target Cargo `babylon60_kernel` | [fuente](../../src/bin/babylon60_kernel.rs) |

Los dos ejecutables llamados `babylon60` pertenecen a interfaces distintas.
`uv run --locked babylon60` selecciona el CLI Python instalado en el entorno;
`cargo run --locked -p babylon60_root --bin babylon60 -- archivo.b60`
selecciona el intérprete Rust. `cortex`, `cortex-persist`, `cortex-compliance` y
`b60_kernel` son nombres históricos, no puntos de entrada publicados por estos
manifiestos. Revise comandos heredados antes de copiarlos.

El paquete Python está marcado `Private :: Do Not Upload`. La declaración de
su nombre no acredita una publicación en PyPI ni autoriza a subir una release.

## Código y contratos de persistencia

- [core/cortex_persist.py](../../01_KISH_ENGINE/babylon60/core/cortex_persist.py)
  contiene la fachada de persistencia y utiliza el
  [esquema core](../../01_KISH_ENGINE/babylon60/core/master_ledger.sql).
- [bft/cortex_persist_ledger.py](../../01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py)
  implementa `CortexPersistLedger`; su
  [kernel criptográfico](../../01_KISH_ENGINE/babylon60/bft/cortex_crypto_kernel.py)
  define el digest de las entradas de ese ledger.
- El [perfil criptográfico](../01_spec/spec_cryptographic_profile.md) distingue
  subsistemas. No intercambie bases ni hashes sólo porque compartan la palabra
  «ledger».
- Las pruebas versionadas residen en [tests/](../../tests/). Un contador en
  documentación no sustituye la ejecución de la revisión evaluada.

## Preparación y comprobaciones

Desde la raíz del checkout:

```sh
uv sync --locked --extra dev --extra gemini
uv run --locked babylon60 --help
uv run --locked babylon60-compliance --help
cargo metadata --locked --no-deps --format-version 1
```

Para cambios documentales, ejecute `make docs-check`. Los cambios de código
requieren las pruebas y los linters dirigidos a sus rutas; las suites completas
están declaradas en [Makefile](../../Makefile) y los flujos de
[CI](../../.github/workflows/ci.yml). Por ejemplo, el paquete Python se analiza
en `01_KISH_ENGINE/babylon60`, no en un directorio `babylon60` de la raíz.

Una salida satisfactoria de `cargo metadata` comprueba el inventario de targets,
no su compilación ni ejecución. La ayuda de un CLI comprueba su interfaz, no
la integridad de un ledger ni las garantías del runtime.
