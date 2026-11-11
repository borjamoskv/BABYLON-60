# Windows: validación del 23 de octubre de 2026

Estado: **NO_VERIFICADO para la revisión actual**. El intento nativo no llegó a
crear un runner ni a ejecutar pruebas. No se ha desplegado ni publicado producto.

## Intento sobre la revisión actual

- [Run Windows 40022207977](https://github.com/borjamoskv/BABYLON-60-VAULT/actions/runs/40022207977),
  `workflow_dispatch`, creado a las 20:49:42 UTC.
- SHA solicitado y observado: `29b100640a41e2fb16738628dc27e293617285a7`.
- Resultado de GitHub: `completed / startup_failure`; cero jobs, check runs y
  artefactos. No hay XML ni JSON de entorno, ni paquete ejecutado verificable.
- El workflow de esa revisión exige seis casos por Python 3.11 y 3.12: tres de
  instalación del ZIP/CLI/MCP y tres de argumentos PowerShell. Conserva identidad
  del SO, arquitectura, versiones, commit y hashes. Es una obligación preparada,
  todavía sin resultado nativo para este SHA.

El push de la misma revisión produjo el
[run 40022187100](https://github.com/borjamoskv/BABYLON-60-VAULT/actions/runs/40022187100),
con `path=BuildFailed`, nombre vacío y el mismo resultado anterior a jobs.
Otros intentos del 23 de octubre, anteriores a esta revisión y correspondientes a
otras ramas, schedules y workflows, también terminaron en `startup_failure`.
Esto no identifica por sí solo su causa.

La API confirma Actions habilitado, `allowed_actions=all` y
`sha_pinning_required=false` en el repositorio. La causa concreta no aparece en
los endpoints de run, jobs, check suite ni check runs inspeccionados. La interfaz
web disponible no tenía sesión GitHub y mostró `404 / Sign in` para este recurso
privado. No se han modificado autenticación, políticas ni facturación, y no se
ha repetido el intento sin diagnóstico.

## Comprobaciones locales y evidencia anterior

PowerShell 7.6.8 oficial para macOS ARM64, descargado a un directorio temporal y
contrastado con el digest SHA-256 publicado en su release: los 18 casos de
`tests/test_first_use_installers.py` pasan sin omisiones. El parser acepta ambos
scripts `.ps1` distribuidos y el nuevo step de evidencia. `actionlint`, whitespace,
presupuesto y topología pasan. La ejecución informa `IsWindows=False` y no
acredita comportamiento nativo de Windows.

Los recibos API y logs locales se conservan fuera del repositorio, bajo
`~/.babylon60/validation/integration-platforms-20261023/windows-run-40022207977/`:
`powershell-macos-tests.log` contiene el resultado de los 18 casos;
`powershell-macos-parser.log` y `powershell-asset.json` identifican parser y descarga;
`windows-workflow-actionlint.json` registra comando, versión y salida cero;
`local-evidence-manifest.json` conserva sus hashes y el comando de pytest.
El log original de las pruebas está en `/tmp/babylon-windows-powershell-tests.log`.

El [run histórico 39649886073](https://github.com/borjamoskv/BABYLON-60-VAULT/actions/runs/39649886073),
del 21 de octubre, sí conserva XML nativo: tres casos pasan, cero fallos y cero
omisiones, tanto en Python 3.11 como 3.12. Su paquete declara la revisión
`d619d05fbfdc620a185dffda748e462de9d17c17`; el SHA-256 descargado y comprobado es
`f733c057f6ac029e6b282a42215a518e7dac5c353a82552caf01eb6d2257c867`.
La comparación con la revisión local encontró 87 archivos distintos, incluidos
instalador, CLI y MCP. Este antecedente no certifica los cambios actuales.

## Actualización del 11 de noviembre de 2026: v5.1.0

Estado para v5.1.0: **NO_VERIFICADO**. El tag `v5.1.0` del repositorio público
apunta a `66ec0e30a8d19b8562e134e3c1eacda404944add`; `RELEASE_MANIFEST.json`
registra el commit de release `e02cc29e7bfea6d987215a30a43fe10ecd397832`. El
árbol no contiene un recibo nativo de Windows para ninguna de las dos revisiones.

En el repositorio público, el workflow `Windows CLI and MCP` registra 37
ejecuciones, todas por `pull_request`, y ninguna terminó con éxito. La más
reciente, el [run 42986022633](https://github.com/borjamoskv/BABYLON-60/actions/runs/42986022633)
sobre `79e79c1` ([PR #62](https://github.com/borjamoskv/BABYLON-60/pull/62)),
falla en el paso «Install archive and verify CLI and MCP» con Python 3.11 y 3.12.
Consulta hecha mediante la API de GitHub Actions el 11 de noviembre de 2026; no
se relanzó ningún workflow ni se diagnosticó la causa del fallo.

El README deja de afirmar que v5.1.0 se validó en Windows. La pasada nativa del
run 39649886073 sigue limitada a la revisión `d619d05`.

## Reanudación

Primero obtener el error de inicio concreto en la página autenticada del run.
Tras resolver ese bloqueo, ejecutar el workflow en una revisión congelada y
exigir `head_sha = source.commit = checkout_commit`, SHA-256 correcto del ZIP,
SO Windows y seis casos sin omisiones por cada versión de Python.
Esta matriz valida distribución terminal, instalación y MCP; no certifica el
workspace Rust completo, Secure Enclave ni el sandbox de `cognitive_pilot` en Windows.

## Residuo de limpieza

Se creó una pestaña temporal del run 40022207977 en Chrome y otra en Brave.
Su cierre quedó pendiente porque la API nativa y su reinicio devolvieron
`Transport closed`. La sesión independiente de Playwright sí quedó cerrada.
No se cerraron pestañas anteriores del usuario ni se intentó autenticación.
