# Revisión de integración · 23 de octubre de 2026

> [!NOTE]
> Este informe conserva el cierre local de `816143b918`. La continuación incluye
> un push a la rama privada de validación y un intento de CI Windows, sin despliegue.
> Véanse [Windows](windows-validation-2026-10-23.md),
> [Linux ARM64](linux-arm64-validation-2026-10-23.md) y
> [evaluación real del piloto](cognitive-pilot-real-evaluation-2026-10-23.md).
> En la continuación, los 24 workflows pasan actionlint estructural.
> `uv lock --check` y `cargo check -q --workspace --locked` pasan en una copia limpia de
> `60c48bcd21`, con lockfiles idénticos antes y después. Las ediciones Rust
> concurrentes permanecen en el árbol del operador y fuera de ese dominio.
>
> El escaneo completo del filesystem encuentra una clave PEM local preexistente,
> ignorada y no trackeada; se conserva sin mostrarla ni añadirla a commits.
> El escaneo de candidatos Git selecciona 2372 archivos sin hallazgos;
> no incluye ese PEM ignorado. Es un dominio distinto del filesystem completo. El permiso local observado es 0644; queda pendiente restringirlo
> por el operador, fuera del diff revisado.

## Alcance y preservación

Revisión del diff local sobre `a25ff27430`, en `codex/integration-review-20261023`,
con agentes separados por kernel, componentes nativos, Python, licencias y Lean,
instalación, CI y biblioteca de skills. La ampliación autorizada incluye
`cognitive_pilot`, memoria persistente y registro de lecciones. La copia inicial y una copia reconciliada
se conservaron fuera del repositorio. Las ediciones concurrentes se incorporaron
tras confirmar el operador que la otra sesión estaba detenida.

No se modificaron dependencias ni lockfiles, ni se desplegó, publicó o hizo push.
Se retiró el ruido de formato introducido durante esta revisión de quince
fuentes Rust, conservando sus cambios iniciales byte por byte. Las correcciones
funcionales de la revisión y el modelo Loom actualizado permanecen.

## Hallazgos corregidos

- El host Chromium terminaba una conexión ociosa; el plazo ahora acota la trama
  desde su primer byte. Se verificaron espera ociosa y drenaje tras calentamiento.
- El transductor podía desalinear la clave IPC respecto del dispatcher; captura
  la clave al crear el canal y rechaza configuración incompleta.
- El cierre dual de Eridu descartaba el servidor secundario; ahora espera ambos
  servidores y propaga errores, incluidas peticiones activas durante el cierre.
- La apertura WORM aceptaba enlaces simbólicos; usa descriptor sin seguimiento,
  fichero regular y permisos privados al crear. La prueba conserva el testigo.
- Un FIFO bloqueaba la lectura de licencia; se abre sin bloqueo y se rechaza
  como fichero no regular. Se alinearon los límites de identificadores Unicode.
- El backend Lean emitía tipos que no aceptaban literales de IR válido; los aliases
  son reducibles y las instrucciones generadas se compilan con Lean fijado.
- El modelo Loom representaba el protocolo anterior; ahora modela CAS y freeze,
  con pruebas de dos escritores y lectores bajo exploración acotada.
- PyPI permitía publicación manual sin verificar gates del SHA; exige main,
  revisión exacta y gates satisfactorios antes de construir y publicar.
- El ZIP omitía el runner documentado y contratos enlazados; ahora los incluye.
  El diagnóstico MCP tiene plazo y número de mensajes acotados.
- La biblioteca de skills tenía enlaces no portables, generación divergente,
  ruta de biblioteca incompleta y modos no deterministas. Se preservó el catálogo
  contextual recibido y se probaron generación, routers y tres distribuciones.
  Al incorporarlo al índice se normalizó whitespace en 408 fuentes canónicas
  y 17 módulos generados, conservando 979 saltos duros Markdown y el AST Python.
- El mantenimiento de skills podía solapar salida e instalación o restaurar sobre
  cambios posteriores. Rechaza esos casos y valida todos los destinos y backups
  antes del rollback. La aplicación y retirada se ejercitaron solo en temporales.
- El cold ledger admitía trabajo después del cierre y el lifecycle podía declarar
  retirada incompleta como éxito. Se corrigieron ambos defectos previos y se
  comprobaron cierre concurrente, drenaje y fallos de limpieza observables.
- Se corrigieron tipos y formato Python y se acotaron guardas heurísticas:
  exclusión mutua de renders por comportamiento; secretos sobre candidatos Git,
  conservando detección de claves trackeadas incluso si coinciden con gitignore.
  Los payloads PNG válidos se excluyen únicamente del detector de entropía;
  patrones de secretos y texto de SVG siguen inspeccionados.

- El piloto admitía artefactos a través de ancestros simbólicos y podía bloquear
  con un FIFO; ahora usa descriptores sin seguimiento y exige fichero regular.
  La publicación durable sincroniza contenido y directorio. Los planes y runs
  fijan membresía, la reclamación concurrente es exclusiva y la retención fallida
  no puede completar una ejecución. Se rechazan valores no finitos, recibos
  inconsistentes, IDs duplicados y contaminación entre conjuntos públicos y ocultos.
- La memoria nueva carecía de la API que usaban las pruebas entrantes. Se añadieron
  filtros SQL parametrizados antes del límite y persistencia optativa sin romper
  la API anterior. La activación de lecciones valida la evidencia bajo la misma
  exclusión transaccional que inserta el evento, evitando carreras de doble activación.

## Evidencia

- Pasada global ampliada final: **2.281 passed, 16 skipped, 1 xfailed y 223 subtests
  passed**, salida 0, 427,06 s. PyO3, binario de autoridad, FFI, envelopes Lean e
  instalación ZIP estuvieron disponibles. No hubo omisiones por falta de PyO3,
  autoridad ni biblioteca FFI. Las 16 omisiones se deben a artefactos Ω-10k/L1,
  revisión humana del modelo ligado, PowerShell/Windows, catálogo oncology y un
  binario legado retirado.

- Pasada Python anterior a la ampliación: **2.105 passed, 22 skipped, 1 xfailed y 223 subtests passed**,
  380,59 s. Biblioteca nativa, envelopes Lean e instalación ZIP fueron obligatorios.
- `make check`: Ruff correcto, 470 archivos con formato y mypy sin errores en 463 fuentes.
- Workspace Rust: `cargo check` y `cargo test --workspace --locked` con salida 0;
  seis pruebas ignoradas según el resumen del runner.
- FFI real: dylib recompilada y cargada, **18 passed**, sin omisiones de biblioteca;
  un caso omitido por manifiesto L1 ausente.
- Lean: build correcto; cinco comparaciones de encoders y compilación de IR válido.
- Loom: **5 passed**, exploración acotada a dos preempciones.
- Skills: **63 passed** en seis archivos; tres distribuciones sin enlaces locales
  rotos ni patrones semánticos conocidos.
- Enlaces y anchors locales de documentación modificada: cero rotos.
- Diez workflows pasan actionlint estructural. La integración opcional con ShellCheck
  no terminó localmente y se detuvo; no se ejecutaron workflows remotos.
- Escáner final: 2.360 archivos seleccionados entre 2.379 candidatos Git, incluido
  este informe, cero hallazgos. Los controles
  negativos verifican rechazo de una clave trackeada y de un secreto nuevo.
- Presupuesto: 22.398 / 40.000 bytes; topología y `uv lock --check` correctos.

- PyO3 y autoridad reales: **11 passed sin skips** en la comprobación independiente.
  Se construyeron `strike_rs` y `babylon_authorityd`; la extensión se cargó desde
  un directorio temporal, sin instalarla en el entorno ni activar servicios.
- Piloto cognitivo: **105 passed**; ejecutor real Seatbelt con candidato controlado,
  canary externo rechazado y bucle interrumpido por timeout. El agente contrastó
  también 2.160 casos de los oráculos del banco con un cálculo independiente.
- Memoria: **61 passed** nuevos; el agente amplió a 117 comprobaciones con
  persistencia, crypto y routing. Se verificaron reapertura, paginación filtrada,
  rollback y una única transición ante 32 escritores concurrentes.
- Tras integrar ambos módulos, los gates detectaron profundidad excesiva en
  `run_one` y dos bucles sin condición explícita. Se extrajo un helper y se
  explicitó la condición de página sin truncar el historial. Comprobación
  conjunta independiente: **185 passed, 1 skipped y 1 xfailed**. El tramo posterior
  completó **1.147 passed, 8 skipped y 194 subtests passed**.
- Una primera pasada ampliada terminó al 69% con código 137 y sin resumen; no
  constituye validación. El diagnóstico con nombres permitió encontrar los gates
  anteriores. El código 137 no se reprodujo en el tramo posterior ni en la pasada
  global final y su causa
  no está determinada.
- El congelado de 2.378 rutas conservó hashes, permisos de ejecución y enlaces
  tras la incorporación de estas dos áreas. Dependencias y lockfiles intactos.


Los comandos reproducibles se ejecutan desde la raíz del checkout:

```sh
uv lock --check
make check
BABYLON60_REQUIRE_NATIVE=1 BABYLON60_REQUIRE_LEAN_ENVELOPES=1 BABYLON_TEST_INSTALL_BUNDLE=1 CARGO_BUILD_JOBS=2 uv run --locked pytest -vv -o addopts= --tb=short -rs
CARGO_BUILD_JOBS=2 cargo check --workspace --locked -q
CARGO_BUILD_JOBS=2 cargo test --workspace --locked -q
CARGO_BUILD_JOBS=2 cargo build --locked -p babylon60_root --lib
BABYLON60_REQUIRE_NATIVE=1 uv run --locked pytest tests/test_exergy_binary_ipc.py tests/test_merkle_cross_bisimulation.py -q
cd proof/lean && lake build
```

La pasada ampliada añade la extensión PyO3 y el binario de autoridad reales.
Se construyen con `cargo build --locked -p strike_rs --features extension-module`
y `cargo build --locked -p babylon60_root --bin babylon_authorityd`. La dylib
`target/debug/libstrike_rs.dylib` se copia a un directorio temporal como
`strike_rs` más `sysconfig.get_config_var("EXT_SUFFIX")`; ese directorio se pasa
por `PYTHONPATH` y el binario compilado por `BABYLON_TEST_AUTHORITY_BIN`.
La extensión no se instala en el entorno. La prueba de autoridad provisiona
identidad IPC efímera solo dentro de su subproceso aislado.

El modelo de concurrencia usa el comando declarado en `CLAIMS.toml`,
`LOOM_MAX_PREEMPTIONS=2`, `--cfg loom`, perfil release y target separado.
La instalación real se probó desde ZIP, offline y sin editable, con setup,
setup repetido, doctor y retirada en un entorno temporal con rutas Unicode.
Codex CLI 0.144.5 confirmó configuración, ejecutable, transporte, contrato y
10 herramientas; las preferencias originales se conservaron.

## Límites

Estas pruebas no certifican biometría Secure Enclave, efectos productivos,
consumo físico, ni aplicación de preferencias por el modelo. No se llamó a un proveedor de modelos ni se ejecutó un estudio real de mejora
cognitiva. El flujo API del piloto se ejercitó con resultados sintéticos; no tiene
CLI. El aislamiento real se comprobó solo en macOS. Transferencia usa nuevas
muestras de las mismas familias, no prueba transferencia a dominios nuevos.
Los IDs de validadores y evidencias de memoria son metadatos suministrados por
el llamador, no autenticación del operador. La memoria y el piloto se validaron
como superficies separadas; el piloto no consume todavía esa memoria.
La evaluación humana del piloto sigue pendiente. Windows PowerShell no estaba disponible.
El cross-check ARM64 Linux se bloqueó por ausencia de aarch64-linux-gnu-gcc.
El perfil raíz sin ninguna feature tiene dos errores ya presentes en la base (sha2 opcional
y receipt::Signer sin sus cfg);
el workspace por defecto y microkernel sí se comprobaron.

No estaba disponible el manifiesto L1 Ω-10k para su comparación. Los enlaces
remotos de skills quedaron explícitamente sin verificar. La recuperación del
mantenimiento de skills tras SIGKILL o corte eléctrico no está certificada. El escaneo del directorio
completo identifica una clave local ignorada; se preservó fuera de los candidatos
Git y no se mostró ni incorporó su contenido. El escaneo de candidatos mantuvo los
controles negativos de secretos y no amplió allowlists de archivos o directorios.

Los trailers de los commits señalan el checkpoint MCP vacío observado en lectura
(raíz de 64 ceros y secuencia 0). No acreditan registrar estos commits en runtime
ni constituyen atestación hardware; su gate comprueba solo sintaxis.

La inspección adicional de FFI detectó una reserva alineada de 64 bytes sin
liberación en `SharedManifestFFIWriter`, ya presente e intacta respecto a la base.
Su vista ctypes pública conserva una dirección prestada; añadir `free` sin revisar
la propiedad introduciría una referencia a memoria liberada. Se registra como
problema previo, fuera de las regresiones del diff. La sonda PyO3 de 16 ciclos
mantuvo cuatro descriptores y unos 21 MiB de RSS; no demuestra ausencia general
de fugas ni explica el código 137.

## Rutas de comprobación

- [Pruebas del piloto cognitivo](../../tests/test_cognitive_pilot_integration.py).
- [Filtros del ledger](../../tests/test_cortex_query_filters.py).
- [Persistencia de metamemoria](../../tests/test_metamemory_persistence.py).
- [Registro de lecciones](../../tests/test_skill_learning.py).
- [Invariantes globales](../../tests/test_c5_invariants.py).

## Commits revisables

- `15397b07e6` — [AX-152] GOVERNANCE: acotar contratos, identidad y evidencia de producto
- `6ac9b8bdc9` — [AX-153] KERNEL: unificar manifest y autenticar efectos con persistencia durable
- `1bd1ee6db4` — [AX-154] NATIVE: integrar IPC acotado y cierre completo de servidores
- `cf4d1f069f` — [AX-155] LICENSE: vincular claims y rechazar entradas inseguras sin bloqueo
- `0e5d09653c` — [AX-156] FORMAL: compilar envelopes y verificar IR Lean contra Rust
- `d4c7fbef88` — [AX-157] RUNTIME: cerrar fronteras Python y preservar estado en pruebas
- `0799edda6b` — [AX-158] SKILLS: preparar mantenimiento verificado con rollback conservador
- `7d74fe45df` — [AX-159] CODEX: activar perfil portable y entregar instalacion comprobable
- `eac4c5b6f1` — [AX-160] CI: exigir gates del SHA y calibrar controles de publicacion
- `bab9390ddc` — [AX-161] SKILLS: converger catalogo contextual y distribuciones reproducibles
- `8aa01be15c` — [AX-162] COGNITIVE: persistir evaluaciones ciegas con ejecucion confinada
- `d51569035b` — [AX-163] MEMORY: persistir memoria y activaciones con precondicion transaccional
- `37d3a2fce6` — [AX-164] INTEGRATION: acotar control de ejecucion y explicitar paginacion

El commit de evidencia posterior incorpora este informe. Ningún commit se envió al remoto.
