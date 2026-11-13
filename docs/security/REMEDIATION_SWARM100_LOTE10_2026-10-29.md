# Lote 10 ejecutado: preservar locks y bases en la purga — 29/10/2026

> Alcance de la distribución pública: las referencias marcadas como material no distribuido identifican evidencia o herramientas excluidas deliberadamente de este checkout. Se conservan sus rutas y los resultados históricos; esos soportes no pueden verificarse desde esta distribución.

C0574 (P1) y C0575 (P2) pasan a FIXED para la selección insegura de locks y
bases de datos durante la purga. La única fuente productiva editada es
`scripts/c5_verifiers/purge_residuals.py`. El
registro reconciliado (material no distribuido: `evidence/swarm100-round3-20261028/registry.json`)
y la validación final (material no distribuido: `evidence/swarm100-lot10-20261029/validation.json`)
conservan estados, comandos, hashes y límites.

## Reproducción y aceptación

Las nueve reproducciones previas (material no distribuido: `evidence/swarm100-lot10-20261029/before-tests.log`)
fallaron contra el hash previsto (material no distribuido: `evidence/swarm100-lot10-20261029/before-source-manifest.json`).
Se observaron desaparición de las rutas de locks abiertos, pérdida de la
exclusión de Git, desaparición de rutas SQLite/WAL/SHM y archivos parecidos, pérdida
de una base dentro de una caché y una afirmación de 0% entropía sin evidencia.
Todo ocurrió en fixtures propias. El fallo de exclusión no acredita corrupción
de ningún repositorio real ni borrado físico de los datos.

**889 pruebas pasan y 1 se omite** en la suite acumulada final, incluidas
**60 regresiones del lote**. La omisión corresponde a strike_rs no compilado,
con el módulo bloqueado antes de recoger los tests. Pasan MyPy con
check-untyped-defs, Ruff y los controles documentales. Fuente y pruebas conservan
sus hashes antes/después de la suite.

La revisión independiente (material no distribuido: `evidence/swarm100-lot10-20261029/independent-review.json`)
aprueba **11 controles en 14 raíces temporales**, repite las 60 regresiones y
Ruff y no deja hallazgos accionables abiertos dentro de estos dos IDs.
Contrasta inode/contenido/exclusión Git, SQLite activa incluso bajo nombre .pyc,
WAL/SHM, sustituciones controladas y reportes de fallos sin falsos borrados.

| ID | Corrección | Efecto observado |
| --- | --- | --- |
| C0574 | Se elimina la selección de locks para unlink y el borrado recursivo de directorios; se excluyen entradas/estructuras Git. | index.lock y packed-refs.lock conservan inodo y contenido con descriptor abierto; Git sigue rechazando un escritor competidor. |
| C0575 | Se retira scratch/*.db* y se preservan bases/auxiliares, cachés opacas y archivos desconocidos. | La base activa, WAL/SHM, archivos parecidos y bases dentro de cachés permanecen intactos; no se ejecuta ningún checkpoint ni disposición de bases. |

## Alcance de la nueva limpieza

La limpieza es deliberadamente más estrecha que la anterior. Solo selecciona
archivos regulares .pyc dentro de __pycache__, del usuario actual, con un único
hardlink y cabecera reconocida de la versión Python en ejecución. Nunca elimina
directorios. Conserva .DS_Store opacos, .pyo, bytecode fuera de __pycache__,
cabeceras desconocidas/truncadas y contenido de cachés no acreditadas. Este
refinamiento previo al parche (material no distribuido: `evidence/swarm100-lot10-20261029/task-contract.md`)
evita que rmtree destruya datos colocados dentro de una carpeta llamada caché.

Git, scratch, dependencias/builds y cachés opacas se excluyen del recorrido.
La detección HEAD/objects/refs o HEAD/commondir/gitdir preserva estructuras de
Git/bare/worktree aunque tengan otro nombre o se elijan como raíz. Una entrada
.git archivo o symlink no se sigue. El recorrido no interpreta esos punteros
ni se amplía a un common-dir externo. El filtro de nombres DB/SQLite/journal,
WAL/SHM y lock se aplica antes de seleccionar cualquier candidato.

El acceso se hace con descriptores relativos y O_NOFOLLOW/O_NONBLOCK, comparando
stat/fstat e identidad/contenido observado antes del unlink. Se preservan
symlinks, hardlinks y tipos especiales. El reporte registra un borrado solo
cuando unlink tiene éxito; un error de recorrido/borrado o de presupuesto se
registra y produce retorno CLI no cero. Hay límites de profundidad y número
de entradas; no se presenta un inventario ilimitado o una purga global.

La API devuelve `babylon60.residual-cleanup.v2`: raíz, alcance, entradas
observadas, borrados, preservaciones y errores. El CLI conserva el modo texto
y añade --json. SCOPED_OK significa que la ejecución terminó dentro de ese
alcance sin errores registrados; no significa que todas las cachés se borraran
ni que el repositorio sea seguro. No se calcula espacio físico recuperado.

Se retira verify_va automático: no demuestra propiedad de un artefacto ni el
resultado de la limpieza y puede producir efectos ajenos. En las reproducciones
originales estuvo sustituido por un stub inerte. La versión final no lo importa
ni lo invoca; declara verification=NOT_REQUESTED y elimina 0% entropía,
repositorio libre y cualquier certificación derivada del listado de borrados.

## Límites y evidencia

- Los primeros 17 bytes permiten reconocer magic/cabecera/flags y presencia de
  contenido, no demostrar procedencia, validez completa de bytecode ni derecho
  universal a borrar un archivo. Un archivo controlado por el caller puede
  satisfacer esa política; se declara la selección concreta, no autenticidad.
- Python no ofrece aquí unlink condicionado atómicamente al inodo previamente
  comprobado. Otro escritor aún puede reemplazar el nombre entre la última
  comprobación y unlink. Las intercalaciones probadas se detectan, sin certificar
  aislamiento frente a todos los reemplazos/renombres hostiles.
- Los descriptores y exclusiones no son un sandbox del sistema operativo ni
  una prueba de contención frente a bind mounts/renombres de ancestros. Árboles
  excluidos y entradas no recorridas no se certifican. Los candidatos de otro
  dispositivo se preservan.
- No se implementa una eliminación autorizada de bases de datos, limpieza de
  locks supuestamente huérfanos, checkpoint, borrado criptográfico o recuperación
  de bloques. La desaparición de un nombre no prueba liberación física.
- Todas las purgas/Git/SQLite se ejecutaron solo sobre fixtures y copias en
  raíces temporales propias, con HOME/configuración Git aislados y TCP/DNS
  prohibidos en las fixtures. El verificador original fue inerte. No hubo purga
  real del proyecto, bases del operador, firma/hardware, runtime protegido,
  publicación o ATTESTED. Se omite la telemetría global.

El control de alcance (material no distribuido: `evidence/swarm100-lot10-20261029/scope-check.json`)
confirma intactos los lotes anteriores, dependencias y lockfiles. Es una
reescritura completa del único script autorizado; no se modificaron otros
archivos productivos.

## Registro y siguiente lote

Los 598 IDs originales quedan en **542 OPEN, 48 FIXED, 4 MITIGATED y
4 NOT_APPLICABLE**. Entre los 582 pendientes iniciales: 537 OPEN, 38 FIXED,
3 MITIGATED y 4 NOT_APPLICABLE. Quedan **536 hallazgos únicos OPEN**:
55 P1, 471 P2 y 10 P3. Solo se cierran C0574/C0575, sin duplicados adicionales.
C0431 y C0135/C0136 siguen OPEN; C0460 sigue MITIGATED.
SW100-R3-0001 permanece FIXED fuera de los 598 IDs.

El [Lote 11 propuesto](PLAN_SWARM100_LOTE11_2026-10-29.md) agrupa C0167/C0168/C0169
en core/cortex_persist.py. Solo se prepara; su fuente conserva el hash seleccionado.

El MCP de grafo está disponible: project babylon-60 y raíz exacta, cobertura
metadata_match como señal best-effort. Se consultaron mediante Context7 las
fuentes primarias de [CPython: operaciones de descriptor](https://github.com/python/cpython/blob/main/Modules/posixmodule.c)
y [CPython: revalidación stat/open/fstat](https://github.com/python/cpython/blob/main/Lib/shutil.py).
Los flags y operaciones se ejecutaron además en las fixtures; no se atribuye
portabilidad a plataformas sin esas primitivas POSIX.
