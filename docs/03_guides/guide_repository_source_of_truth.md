---
title: Fuente de verdad del repositorio y la distribución
status: Referencia de implementación
version: 1.1.0
---

# Fuente de verdad del repositorio y la distribución

BABYLON-60 es el proyecto. El nombre de la distribución Python y del paquete
importable es `babylon60`. La CLI principal se llama `babylon60` y el servidor
de memoria por stdio se llama `babylon60-mcp`. Estos nombres están declarados
en [`pyproject.toml`](../../pyproject.toml); `cortex-persist` y `cortex` no son
los nombres de instalación ni los comandos principales de esta distribución.

## Fuentes de implementación

| Superficie | Fuente |
| --- | --- |
| Nombre, versión, dependencias y ejecutables Python | [`pyproject.toml`](../../pyproject.toml) |
| Paquete Python | [`01_KISH_ENGINE/babylon60`](../../01_KISH_ENGINE/babylon60) |
| Despachador de la CLI | [`main_dispatcher.py`](../../01_KISH_ENGINE/babylon60/cli/main_dispatcher.py) |
| Servidor de memoria MCP | [`cortex_mcp_server.py`](../../01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py) |
| Ledger que utiliza el servidor MCP | [`bft/cortex_persist_ledger.py`](../../01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py) |
| Pruebas Python configuradas | [`tests`](../../tests) y [`02_EDIN_SWARMS/tests`](../../02_EDIN_SWARMS/tests) |
| Contenido del paquete fuente de instalación | [`scripts/package_release.sh`](../../scripts/package_release.sh) |
| Controles de integración y distribución | [Workflows de CI](../../.github/workflows) |

Los nombres internos que conservan `cortex` no implican que exista un ejecutable
`cortex`. El ejecutor Rust de archivos `.b60` tiene su propio nombre,
`babylon60-dsl`, según [`Cargo.toml`](../../Cargo.toml).

## Instalación y comprobación

El [README](../../README.md#-quickstart--installation) describe la instalación
de CLI y memoria MCP. Para activar el cliente Codex, seguir la
[guía de primera conversación](guide_codex_first_use.md). Una vez instalado:

```sh
babylon60 --help
babylon60 --version
babylon60 doctor --client codex --json
```

`doctor` informa de la integración local y del transporte MCP. Su resultado
no certifica las garantías del kernel ni demuestra por sí solo que un modelo
aplique las preferencias durante una conversación.

Para desarrollar, ejecutar las pruebas y los controles configurados para las
rutas afectadas. Por ejemplo, desde un entorno de desarrollo preparado:

```sh
uv run --locked pytest tests/test_first_use_cli.py tests/test_codex_onboarding.py -q
uv run --locked ruff check 01_KISH_ENGINE/babylon60/cli/main_dispatcher.py
```

Estos comandos son comprobaciones dirigidas; el conjunto requerido para una
revisión lo definen los workflows y el [contrato de trabajo](../../AGENTS.md).
Las pruebas con componentes nativos requieren también las compilaciones y
variables de entorno declaradas en el workflow correspondiente.

## Alcance de una versión

El paquete fuente de CLI/MCP y el wheel Python tienen contenidos definidos por
sus respectivas reglas de empaquetado. La existencia de un archivo descargable,
un badge o una receta de pruebas no acredita una ejecución satisfactoria.
La evidencia debe identificar revisión de código, archivo distribuido, digest,
entorno y resultado. Consultar [`CLAIMS.toml`](../../CLAIMS.toml) para el alcance
y los límites de cada garantía; las propiedades pendientes permanecen
`NO_VERIFICADO` hasta su comprobación.
