# Z3 — instalación compatible y cierre de la salvedad

**Salvedad de Z3 resuelta en los entornos comprobados.** Las instalaciones
limpias de macOS ARM64 con Python 3.11, 3.12 y 3.14 terminan sin avisos de
incompatibilidad; `uv pip check` y `python -m pip check` devuelven cero.
También pasa la reconstrucción completa de la imagen Linux ARM64 con Python
3.14. H08 y la validación remota de H09 siguen pendientes. No se hace merge.

Esta iteración de la [PR #48](https://github.com/borjamoskv/BABYLON-60/pull/48)
parte de `c15cf7be1042c9c2fdde89cfea0392c93b8d7c8a`. El diagnóstico upstream,
la revisión de consumidores, la instalación limpia y Docker se repartieron
entre agentes distintos. Los cambios de dependencia se prepararon en una copia
limpia aislada y sus bytes verificados se integraron después.

## Causa y corrección

Z3 5.1.0.0 podía importar y resolver problemas, pero su wheel macOS tenía un
nombre con `macosx_13_0_arm64` y metadatos internos con `macosx_13_3_arm64`.
El segundo tag no pertenece al conjunto compatible generado por el intérprete.
Por eso un smoke SAT pasaba mientras `uv pip check` fallaba.
La [incidencia upstream](https://github.com/Z3Prover/z3/issues/10689) documenta
el problema; la [corrección de normalización](https://github.com/Z3Prover/z3/pull/11300)
está presente en los wheels oficiales desde 5.3.2.0.

- Base y extra dev exigen ahora `z3-solver>=5.3.2.0`; el lock selecciona
  [5.3.3.0 oficial](https://pypi.org/project/z3-solver/5.3.3.0/).
- Z3 es el único paquete cuya versión cambia. El conjunto permanece en 203
  paquetes; solo cambia además la declaración de requisitos del proyecto.
- Los wheels ARM64 y x86_64 5.3.3.0 tienen nombres y WHEEL coherentes. Los dos
  archivos completos coinciden con sus SHA-256 oficiales. No se retoca ningún
  wheel, WHEEL, RECORD ni conjunto de tags del intérprete.
- Se añade `uv pip check` después del sync en los jobs Python y de evidencia
  macOS existentes, y en el builder Docker. Nombres y condiciones de los jobs
  se conservan; esto no acredita una ejecución remota de H09.
- Un test comprueba el WHEEL instalado, su compatibilidad con el intérprete y
  su correspondencia con el wheel compatible del lock, cuando existe. Incluye
  rechazo del tag roto y SAT/UNSAT reales. El entorno antiguo reproduce el
  fallo; el nuevo pasa las tres pruebas.

## Instalaciones limpias comprobadas

Host real: macOS 26.6.2 ARM64; uv 0.13.5 y pip 26.3 como comprobador.
Se instalaron el proyecto y las dependencias del lock, con HOME y estado
aislados y sin credenciales heredadas.

| Python | Perfil | uv pip check | pip check | Z3 nativo y tags |
| --- | --- | --- | --- | --- |
| 3.11.16 | base | 0 | 0 | PASS |
| 3.11.16 | dev + gemini | 0 | 0 | PASS |
| 3.12.14 | base | 0 | 0 | PASS |
| 3.12.14 | dev + gemini | 0 | 0 | PASS |
| 3.14.7 | base | 0 | 0 | PASS |
| 3.14.7 | dev + gemini | 0 | 0 | PASS |
| 3.12.14 | dev + gemini directamente desde vacío | 0 | 0 | PASS |

Cada fila verifica distribución 5.3.3.0, solver nativo 5.3.3, SAT, UNSAT,
modelo entero y BitVec64. El WHEEL instalado conserva el tag oficial
`py3-none-macosx_13_0_arm64`, compatible con el mismo intérprete. Los logs
finales no contienen avisos de instalación o incompatibilidad. El inventario
ampliado desde base coincide con el instalado directamente desde vacío.

También se instaló el wheel final no editable en un entorno nuevo Python 3.11,
con dependencias exportadas del lock y sin resolver versiones libremente.
Ambos comprobadores y el solver pasan. Fuera del checkout y sin PYTHONPATH,
el cliente SDK MCP 2.3.0 verifica initialize, 13 herramientas, seis recursos,
lectura, ping y cierre EOF con salida cero. El servidor procede de site-packages.

Wheel del proyecto SHA-256:
`384376a3a2dee315cbc8bb2f24326efe779b50a4d9a3e35c3bab4062fa17cf9b`.
Sus requisitos publicados incluyen el nuevo mínimo de Z3, también en dev.

## Linux, regresiones y controles

La imagen de producción se reconstruye sin caché con el Dockerfile y lock
actualizados: Python 3.14.10, Linux ARM64, glibc 2.41. El nuevo `uv pip check`
del build pasa; la comprobación adicional del contenedor final observa 27
paquetes compatibles sin avisos de uv. UID 1000, Z3 5.3.3, SAT/UNSAT, CLI,
MCP/EOF y dashboard HTTP/healthcheck pasan. No se monta estado del host ni se
habilita red exterior durante las pruebas. Imagen local conservada:
`sha256:1d9c7d5f577e50116e4cd8e6197ef5b13ca1b81003f9c497343d69c54cf5eaaf`.
El perfil de prueba queda detenido y el contexto original no cambia.

La batería ampliada pasa **603 pruebas Python y 94 subtests**; otros **11 casos
dirigidos** de consumidores de Z3 pasan: **614 pruebas en total**. Se mantienen
tres skips PowerShell y uno del puente nativo por falta de su biblioteca; ese
skip no se cuenta como integración nativa verificada. Las seis deselecciones
originales y las 27 del filtro dirigido se declaran por separado.

Las 24 auditorías de seguridad base/extras para Linux/macOS/Windows y Python
3.11–3.14 terminan con cero vulnerabilidades y estados adversos. Ruff, MyPy,
actionlint, lock, guards documentales y enlaces pasan. La topología del índice
se verifica antes del commit. Configuración global y telemetría de listeners
quedan fuera del alcance documental, expresamente.

```sh
uv sync --locked --extra dev --extra gemini
uv pip check
uv run --locked pytest tests/test_z3_distribution_contract.py tests/test_z3_firewall.py tests/test_ns_z3_firewall.py tests/test_ns_z3_resource_exhaustion.py -q
```

`python -m pip check` se ejecuta adicionalmente en los entornos de validación
provistos de pip; pip no pasa a ser una dependencia de la aplicación.

## Evidencia histórica y límites

El primer seed de herramientas de Python 3.11 incluía wheel/setuptools/packaging.
El sync exacto retiró packaging y dejó wheel, causando un fallo de herramientas
ajeno a Z3. Se conserva aquel fallo y se recrea el entorno con pip como único
comprobador antes del sync; sus filas finales pasan sin añadir dependencias al
proyecto ni ocultar avisos. El aviso de obsolescencia del builder Docker legacy
se distingue de las comprobaciones de instalación de dependencias, que pasan.

Los binarios macOS de esta versión requieren **macOS 13.3 o posterior** según
sus encabezados Mach-O; el tag normalizado 13_0 no certifica ejecución en
13.0–13.2. La ejecución nativa aquí se comprueba en macOS 26.6.2 ARM64; los
wheels Intel solo se inspeccionan. Tampoco se certifican Windows o Linux
Python 3.11/3.12: un ensayo complementario 3.11 se canceló por presión de
recursos del host y 3.12 se omitió. La resolución/auditoría de esos destinos no
equivale a ejecución de sus binarios.

Los comandos, hashes, fallos iniciales, inventarios y logs completos se conservan
en el expediente local; no se distribuyen con este documento. No se renueva el
release histórico ni se publica una imagen en un registro. H08 y H09 remoto
siguen pendientes, sin cambios a pagos o protecciones y sin merge ni auto-merge.
