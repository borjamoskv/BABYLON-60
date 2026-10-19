# Puente MCP local del kernel

`tools/babylon60_mcp.py` expone seis herramientas por `stdio`. Está separado del
servidor de memoria `babylon60-mcp` existente. Necesita Python 3.11 o posterior.
Se ha probado con Python 3.14, FastMCP 4.1.0 y blake3 1.0.11.

## Conectar en tres pasos

1. Desde la raíz del repositorio, prepara un entorno independiente. Estos comandos
   no regeneran `uv.lock`, `Cargo.lock` ni el entorno Python principal:

   ```sh
   uv venv --python 3.14 target/kernel-mcp-venv
   uv pip install --python target/kernel-mcp-venv/bin/python 'fastmcp==4.1.0' 'blake3==1.0.11' 'pyjwt>=2.15.1'
   ```

2. En un cliente local compatible con MCP, registra un servidor `babylon60-kernel`
   cuyo ejecutable sea la ruta absoluta de `target/kernel-mcp-venv/bin/python` y
   cuyos argumentos sean la ruta absoluta de `tools/babylon60_mcp.py`, `--root` y
   la raíz absoluta del checkout. Ejemplo de estructura:

   ```json
   {
     "mcpServers": {
       "babylon60-kernel": {
         "command": "/RUTA/BABYLON-60/target/kernel-mcp-venv/bin/python",
         "args": ["/RUTA/BABYLON-60/tools/babylon60_mcp.py", "--root", "/RUTA/BABYLON-60"]
       }
     }
   }
   ```

   Usa rutas reales en los cuatro campos. La instalación local de esta tarea
   deja el fragmento concreto en `target/kernel-mcp-config.json`. No se mezcla
   automáticamente con la configuración de ningún cliente. Un navegador remoto
   no puede conectarse a este proceso `stdio`; no hay opción `--http`.

3. Comprueba que aparecen las seis herramientas y lee `src/spsc_ring.rs` con
   `read_source`. El Skill portable está en
   `tools/skills/babylon60-kernel-invariants/SKILL.md`; el enlace de descubrimiento
   local está en `.agents/skills/babylon60-kernel-invariants`.

## Capacidades y límites

| Herramienta (Legacy Default) | Alias Funcional (`--use-canonical-names`) | Resultado y alcance |
| --- | --- | --- |
| `read_source` | `kernel_source_read` | Hasta 200 líneas y revisión BLAKE3 del archivo completo. |
| `apply_atomic_patch` | `kernel_patch_apply` | Un reemplazo exacto, revisión esperada, escritura temporal, fsync y rename en el mismo directorio. Requiere `--allow-patches`. |
| `run_nemesis_and_cargo` | `kernel_tests_run` | Target real `adversarial_nemesis` del paquete `babylon60_root`, con `--locked --offline`. Filtro opcional de nombre, sin flags arbitrarios. |
| `audit_spsc_miri_arm64` | `kernel_miri_audit` | Target anterior filtrado por `spsc`, nightly, proveniencia y alineación estrictas; modelos `stacked` o `tree`, target `aarch64-apple-darwin`. |
| `verify_lean4_bijection` | `kernel_lean4_verify` | Fuentes Lean versionadas de `proof/lean`, preflight de tokens prohibidos y `lake --wfail --no-cache build`. No demuestra biyección. |
| `inspect_sqlite_l0_invariants` | `kernel_sqlite_inspect` | Esquema de una exportación SQLite offline, deserializada en memoria. No certifica el estado del escritor ni ejecuta SQL del cliente. |

Por compatibilidad regresiva (Ley `B1: NAME != IDENTITY`), `tools/list` expone por defecto los nombres de la primera columna; añade `--use-canonical-names` (o `BABYLON60_MCP_CANONICAL_NAMES=1`) tanto en `tools/babylon60_mcp.py` como en `babylon60-mcp` para publicar los nombres funcionales `kernel_*` y `cortex_*` como primarios. En modo HTTP (`--transport openapi-http`) o llamada directa sobre `KernelHarness` y `CortexMCPServer`, ambos identificadores se aceptan simultáneamente.

Para inspeccionar desde terminal el catálogo completo de herramientas MCP y las 25 habilidades declarativas del workspace:

```sh
uv run babylon60 tools
uv run babylon60 skills status
uv run babylon60 skills list --scope workspace
uv run babylon60 skills route --query "socratic-interrogator"
```

Lectura por defecto. Los parches y la ejecución se habilitan mediante argumentos
del proceso, no mediante una herramienta MCP. No se implementa atestación hardware,
ingesta al ledger ni lanzamiento del kernel productivo.

Las lecturas aceptan `.rs`, `.lean`, `.sql`, `.toml` y `.py` bajo `src`, `crates`,
`00_ABZU_KERNEL`, `01_KISH_ENGINE`, `proof` y `tests`; también permiten leer los
manifiestos raíz `Cargo.toml` y `pyproject.toml`. Los parches excluyen TOML y
lockfiles. Se rechazan rutas absolutas, `..`, componentes ocultos, directorios
generados, symlinks interiores, hardlinks y archivos no regulares. La raíz puede
ser un symlink lógico elegido por el operador. La apertura usa descriptores de
directorio y `O_NOFOLLOW`; el límite por fuente es 1 MiB.

La revisión detecta parches obsoletos y se comprueba de nuevo antes del rename.
Las operaciones del servidor se serializan. Detén otros editores mientras aplicas
un parche: ningún rename portable implementa compare-and-swap frente a escritores
externos, ni ofrece aislamiento frente a un proceso local hostil que mueve árboles
de directorios. El modelo de confianza incluye el operador local y el checkout.

**Activar `--allow-execution` ejecuta código del repositorio con los permisos del
proceso. Este puente no es un sandbox del sistema operativo.** Cargo, build scripts,
tests y configuración de Lake pueden acceder a recursos fuera del repositorio.
Usa un checkout revisado y, si necesitas aislamiento de procesos, un sandbox del
sistema o una VM. `--offline` limita Cargo, no impide la red de los tests.

Las tres herramientas de ejecución exigen un worktree Git limpio. Si hay cambios,
prepara y revisa un checkout separado; el puente no limpia, confirma ni publica
cambios automáticamente. Prepara dependencias, `protoc`, nightly/Miri y los paquetes
Lean antes de ejecutar. Lake requiere `lake-manifest.json`; no se invoca `lake update`.
Una instalación o FFI incompatible se informa como fallo. Las pruebas SPSC actuales
de NEMESIS cubren `HardenedSpsc`, no automáticamente `SpscRingBuffer`.

Cada proceso tiene un plazo (180/240/300 segundos), 128 KiB de salida combinada y
un grupo de procesos propio, terminado al acabar o superar límites. Los estados
`failed`, `timeout`, `output_limit`, `unavailable` y `no_tests` no cuentan como pase.
Un `completed` solo corresponde a la ejecución indicada; nunca certifica el kernel.

SQLite acepta exportaciones de hasta 16 MiB bajo `proof/`, `reports/` o `tests/`.
Rechaza sidecars `-wal`, `-shm`, `-journal` y archivos con cabecera WAL. Usa una
exportación offline coherente en formato rollback journal, sin añadir bases de datos
al control de versiones. No fuerces un checkpoint del ledger activo mediante el
puente. Se devuelven como máximo 200 tablas/triggers, con indicador de truncamiento.
Las propiedades `synchronous=FULL`, frescura, inmutabilidad y linealización requieren
pruebas del escritor; listar SQL no las demuestra.

## Verificar el puente

Instala `pytest`, `ruff` y `mypy` en un entorno de pruebas independiente. Ejecuta:

```sh
python -m pytest --noconftest tests/test_kernel_mcp_bridge.py -q
ruff check tools/babylon60_mcp.py tests/test_kernel_mcp_bridge.py
mypy tools/babylon60_mcp.py
```

`--noconftest` evita el fixture global que elimina bases de datos de la raíz.
Estas pruebas crean sus propios directorios temporales. Incluyen conexión MCP real,
escapes de ruta, cambios concurrentes, estrés tras calentamiento, fallos de rename,
límites del proceso e inspección SQLite sin modificar el archivo. Los ejecutables
simulados de Cargo/Lake prueban argumentos y propagación de errores; no sustituyen
la suite nativa del kernel.

Referencias de API: [herramientas FastMCP](https://gofastmcp.com/servers/tools),
[Miri](https://github.com/rust-lang/miri),
[Lake](https://lean-lang.org/doc/reference/latest/Build-Tools-and-Distribution/Lake/).
