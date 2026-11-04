# Validación Linux ARM64 — 2026-10-23

## Dominio ejecutado

La fuente base es `816143b918a74a7cd0ed696c2acb23e79fbc0a14`, copiada mediante
`git archive` y un pack Git superficial del mismo árbol. El checkout de pruebas
conservó ese SHA y los dos lockfiles originales. Los cuatro tests portables y
el runner se prepararon aparte y quedaron en `59cf92333e`; la capa posterior del
piloto se tomó de `e0c89a5bf0` y el ajuste de presupuesto del test FFI de
`27b73bf177`. El manifiesto de evidencia distingue esas capas del árbol base.
Se excluyeron las ediciones Rust concurrentes sin commit. La ejecución ocurrió en un
guest Linux ARM64 bajo virtualización de Apple; no fue una compilación cruzada
ni una ejecución en una máquina física con Linux instalado directamente.

| Superficie | Observación |
| --- | --- |
| Host | Apple M3 Pro, macOS ARM64 |
| Virtualizador | Colima 0.10.3 / Lima / Apple Virtualization.Framework (`vz`) |
| Guest | Ubuntu 24.04.4 LTS, kernel `6.8.0-117-generic`, `aarch64` |
| Recursos | 2 CPU virtuales, 3 GiB RAM, discos acotados a 8 + 16 GiB |
| Contenedor | Docker Engine 29.5.2, `linux/arm64`, 2 CPU, 2560 MiB, 512 PIDs |
| Imagen base | `docker.io/library/rust@sha256:0e2bcaef56d041a486784e54104a81aebe0da44bd03019bd70bc0401e42e4a97` |
| Herramientas | Rust 1.97.1, Python 3.11.2, uv 0.12.0, protoc 3.21.12, lsof 4.99.4, Node 20.19.2 |
| Verificación adicional | Lean 4.34.0-rc2 ARM64, elan 4.2.4, Gitleaks 8.30.1 ARM64 |
| Bibliotecas C | glibc 2.41 del repositorio oficial Debian trixie dentro del contenedor efímero |

El perfil `babylon-integration-arm64` se creó sin montajes del host, reenvío de
agente SSH, binfmt, Kubernetes, exposición de puertos de aplicación ni cambio
del contexto Docker predeterminado. El contenedor recibió solamente el árbol
Git y las herramientas de prueba. Su red externa se desconectó después del
provisionamiento. Las pruebas de IPC usaron sus propios recursos locales.

SHA-256 del archivo comprimido de imagen descargado por Colima:
`1fc0354f4f99734ce3886628cc7af8b0437c1a1d391b126bd09cba0df35ee53f`.
Estos hashes identifican artefactos; no son una atestación hardware.

## Reproducción y comprobaciones

El [gate Linux ARM64](../../scripts/validation/validate_linux_arm64.sh) rechaza
otros sistemas operativos o arquitecturas y exige las herramientas de la tabla.
En un guest desechable ya provisionado, sin credenciales productivas y con su
hook local preparado mediante `scripts/c5_git_utils/install_git_hooks.py`:

```bash
bash scripts/validation/validate_linux_arm64.sh /tmp/linux-arm64-evidence
```

El gate sincroniza dependencias con `--locked`, comprueba el lock Python,
ejecuta `cargo check --workspace --locked`, los tests Rust serializados y la
suite Python completa. Compila las pruebas Lean con su toolchain fijado y exige
sus comparaciones desde Python. Construye y carga `libbabylon60.so`, `strike_rs` PyO3 y
el binario real de autoridad para sus fixtures aislados. Guarda versiones,
hashes, logs y JUnit fuera de las fuentes. Usa un directorio temporal ejecutable
propio junto a la evidencia, sin cambiar las opciones de montaje del sistema.
Fija `ELAN_TOOLCHAIN` desde el pin del proyecto para los tests Rust que invocan
Lean desde otro directorio. Tras la sincronización bloqueada usa `uv run
--no-sync`, de modo que la fase de pruebas no requiera resolver de nuevo el
backend de construcción cuando se desconecta la red.

El gate completo terminó con código 0. Python: **2272 casos pasan, 59 se
omiten, 1 tiene fallo esperado y 223 subtests pasan**, en 387,95 s. El log Rust
registra **618 casos que pasan, 0 fallos y 6 ignorados**; `cargo check` del
workspace con `--locked`, build Lean de 19 jobs, nativos y ZIP offline pasan.
Las 2386 rutas congeladas conservaron sus contenidos y permisos hasta el cierre.
El XML conserva las causas de las omisiones: macOS/Seatbelt/CryptoKit,
publicación exclusiva, PowerShell o el archivo de fuentes de CI Windows,
artefactos Ω-10k, catálogo oncológico, laboratorio npm nativo, binario heredado
eliminado y revisión humana del vínculo Lean con el ledger. El fallo esperado
es el advisory sobre SIGKILL. Los 6 ignorados Rust requieren workspaces Lean
preparados, una fixture Swift o exportaciones explícitas de laboratorio; no se
contabilizan como casos que pasan.

El dominio corresponde a base `816143b918` + Linux `59cf92333e` + piloto V2
`e0c89a5bf0` + test FFI `27b73bf177`; no certifica todo el HEAD posterior.

Después del global se copió exclusivamente el paquete del piloto y sus tres
tests desde V3 `287c3d2dc0`: **141 casos pasan, 3 se omiten por Seatbelt**, Ruff
pasa y mypy estricto no encuentra errores en 12 archivos. Se compararon sus
12 hashes con el commit, sin diferencias. Esta capa no repite el global V2 ni
contiene inferencia real en Linux.

Se compiló además `lake build babylon_aot_oracle` (6 jobs) y se comprobó que
produce un ELF64 AArch64. Con ese ejecutable presente, los 15 tests FFI pasan:
la salida propia del programa Lean registra la aceptación de la traza válida y
el rechazo de dos comienzos de escritura consecutivos. La inversión Lamport
se rechaza previamente en Z3. Así se distingue esa ejecución del fallback Rust
usado cuando falta el binario Lean. Son trazas pequeñas de prueba, no una
certificación universal del modelo ni de acceso físico a memoria.

El pase global anterior se conserva: 2236 casos pasan, 2 fallan, 59 se omiten,
1 tiene fallo esperado y 223 subtests pasan (573,63 s). Los dos fallos se
diagnosticaron y comprobaron por separado:

- La FFI rechazó una traza válida con `Z3_INCONCLUSIVE: canceled` al agotar el
  presupuesto productivo de 50 ms. El test de corrección ahora declara 2000 ms
  y conserva el solver real; producción continúa a 50 ms y mantiene el rechazo
  ante resultado inconcluso. Pasaron los 15 tests de FFI y, tras 2 warmups,
  16 ejecuciones separadas del caso afectado. No se certifica latencia
  productiva de 50 ms en este guest.
- El instalador ZIP offline seleccionó el sdist de Z3 pese a tener disponible
  una wheel cacheada. Se invalidaron exclusivamente las caches de Z3 e
  intérprete del contenedor y se recargó la wheel bloqueada. La secuencia apunta
  a metadatos de plataforma anteriores al cambio de glibc; esa atribución es
  una inferencia del diagnóstico, no una inspección del formato interno de uv.
  La instalación sin red y el primer `initialize` MCP pasaron junto con los
  15 casos de FFI (16 casos dirigidos). No se cambió el instalador ni el lockfile.

La capa V2 del piloto pasó 133 casos y omitió sus 3 ejecuciones Seatbelt,
exclusivas de macOS. Ruff y mypy estricto no encontraron errores en sus 12
archivos revisados. Es validación de API, planificación y fixtures HTTP; en
Linux no se llamó a ningún proveedor ni se midió eficacia del modelo.

## Obstáculos diagnosticados

1. El target Rust ARM64 Linux ya estaba instalado en macOS, pero el enlace
   cruzado de `strike_rs` requiere `libpython3.11` del target. Ese intento no
   acredita ejecución Linux y se sustituyó por el guest nativo ARM64.
2. La imagen Debian bookworm original tenía glibc 2.36. La wheel ARM64 de
   `z3-solver==5.1.0.0` fijada en `uv.lock` requiere `manylinux_2_38`; el fallback
   de fuente falló porque GCC 12 no ofrece `<format>`. El provisionamiento
   efímero de GCC 14 desde Debian trixie añadió glibc 2.41, tras lo cual uv pudo
   usar la wheel bloqueada y se comprobó `z3.get_version_string() == "5.1.0"`.
   No se modificaron versiones de dependencias ni lockfiles. Debian 12 sin ese
   provisionamiento sigue fuera del dominio validado.
3. Docker montó `/tmp` con `noexec`, impidiendo la fixture de proceso del
   adaptador Apple. Se usó `TMPDIR` ejecutable en el filesystem de construcción
   del contenedor; no se desactivó el control del host ni se invocó biometría.
4. La ausencia inicial de `lsof` degradaba correctamente la visibilidad del
   observador a incompleta; dos pruebas exigían visibilidad completa. Se añadió
   la herramienta al contenedor y el gate la exige explícitamente.
5. La extracción inicial del archivo Git como root preservó permisos de grupo
   de tar (`0664`/`0775`) que no representa un checkout ordinario. Se normalizaron
   únicamente los archivos inventariados por Git a `0644`/`0755`, según su bit
   ejecutable, y sus directorios a `0755`. El test de distribuciones de skills
   volvió a comparar el contenido y los permisos esperados.

Se corrigieron expectativas de tests, sin añadir un backend de ejecución Linux:
la firma y la telemetría aceptan `No medido` cuando faltan sensores; las dos
integraciones MCP exigen rechazo `OS_ISOLATION_UNAVAILABLE`, ningún lanzamiento
por la API observada, directorio efímero vacío y registro SQL purgado. En macOS
conservan la ejecución real y su salida comprobada. La prueba del hash de elan
usa un `uname` de fixture para llegar al caso de runner declarado; no altera la
identidad del guest ni se usa como evidencia de ejecución ARM64. Esta regresión
dirigida pasó en Linux (78 casos, 6 subtests) y macOS (15 casos, 2 subtests).

Los binarios adicionales se descargaron de las publicaciones oficiales y se
comprobó SHA-256 antes de extraerlos:

| Publicación | Archivo ARM64 Linux | SHA-256 |
| --- | --- | --- |
| [Lean 4.34.0-rc2](https://github.com/leanprover/lean4/releases/tag/v4.34.0-rc2) | `lean-4.34.0-rc2-linux_aarch64.tar.zst` | `64b41db6c158163e53a40ff950cdc978f3892cb11128a4ee050e4de8e8721894` |
| [elan 4.2.4](https://github.com/leanprover/elan/releases/tag/v4.2.4) | `elan-aarch64-unknown-linux-gnu.tar.gz` | `05febd124d84ebf994b2e7479922a5650b1e950c17ae3bd1ddd776b65bb72bf9` |
| [Gitleaks 8.30.1](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1) | `gitleaks_8.30.1_linux_arm64.tar.gz` | `e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080` |

Hashes conservados:

```text
Cargo.lock 6feb30a642ee2fa6ca16dd6f73d01713104738a440d9d98a6e528c22c8307eb7
uv.lock    d78739746ac5d442a074ad73cbc7fc06d6e803558126f65fbc3d6d251d4c1fb4
```

## Límites

La suite prueba los contratos que efectivamente ejecuta en este guest y declara
por separado los casos omitidos. No acredita biometría Secure Enclave en Linux,
aislamiento universal, consumo energético ni prestaciones de un servidor ARM64
físico. Los casos macOS no ejecutados conservan su alcance específico. El
confinamiento de programas de `cognitive_pilot` debe evaluarse por backend; una
prueba de su API o de sus recibos no demuestra que exista un backend Linux.

La validación Linux se ejecutó localmente sin requerir publicación ni CI remota;
no se desplegó el producto.
El perfil efímero se detuvo y se eliminó con sus discos tras exportar la evidencia.
El recibo de limpieza comprueba ausencia del perfil y conservación del contexto
Docker predeterminado.

## Evidencia local conservada

El [paquete local de evidencia](/Users/borjafernandezangulo/.babylon60/validation/integration-platforms-20261023/linux-arm64-evidence-20261023.tar.gz) contiene los logs completos del primer
pase, el pase rojo de 2 fallos, el global verde V2, el delta V3, la ejecución del oráculo
Lean, los manifiestos de fuentes y el recibo de limpieza. El paquete guarda logs
y metadatos; no contiene los binarios ni un nuevo checkout de fuentes y no se
ha publicado.

SHA-256: `d2d7057e2fd2677813ad47f454119cd0a8e2f99bb1c82a1caa9898163afcdd47`.
