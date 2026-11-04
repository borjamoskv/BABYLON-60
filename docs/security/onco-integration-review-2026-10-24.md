# Contraste de la integración oncológica — 24 de octubre de 2026

## Contrato

Resultado: conectar únicamente con relaciones y reglas explícitas existentes;
si no hay una base válida, retirar el componente de la distribución.
Rutas: dispatcher, empaquetador del ZIP, pruebas y este informe. Conservar las
exclusiones del wheel ya presentes y el trabajo ajeno. No modificar dependencias,
lockfiles ni datos biológicos. No realizar una revisión clínica del catálogo.

Aceptación: wheel y ZIP sin los módulos oncológicos excluidos; ayuda sin `onco`
ni `boolean-sim`; ambos comandos rechazados como desconocidos sin traceback.

## Evidencia y correcciones del informe recibido

Se consultó el grafo del proyecto `babylon-60`, raíz `BABYLON-60`, y la cobertura
de ambos módulos. Se contrastaron las fuentes y referencias textuales en el
repositorio, incluidos scripts, pruebas, generadores y empaquetadores.

- El [glosario](../../01_KISH_ENGINE/babylon60/oncology_primitives.py) tiene
  300 registros, 17 categorías y 155.493 bytes. Sus cinco consultas son de datos;
  `search()` compara subcadenas. También tiene ejecución directa bajo `__main__`.
- Weinberg 2014 aparece en 195 registros. Hay 90 cadenas de referencia distintas
  en total, no 16. Los 300 registros declaran `C5-established`.
- `ONCOLOGY_PRIMITIVES_EDGES` no existe. En
  [run_simulation](../../01_KISH_ENGINE/babylon60/cli/onco_transducer.py),
  `graph=None` añade auto-bucles y `getattr(..., [])` devuelve una lista vacía sin
  excepción. El bloque `except` solo registra un mensaje de depuración si hay
  una excepción; no interviene al faltar el atributo con ese valor por defecto.
- La CLI sí estaba conectada: el dispatcher anunciaba `onco` y `boolean-sim`.
  Ese recorrido llama a `execute_pipeline()`, que construye otro grafo por
  correlación, y no a `OncologyTransducer.run_simulation()`. Por tanto, el fallo
  de auto-bucles no describe todos los recorridos del módulo.
- Hay otro importador del glosario en el repositorio:
  [verify_oncology_primitives_dag.py](../../scripts/c5_verifiers/verify_oncology_primitives_dag.py).
  Sus comprobaciones de categorías y subcadenas no aportan aristas ni reglas
  de actualización para el transductor. La ausencia de `__all__` tampoco prueba
  que un módulo sea inaccesible.
- No se encontró una definición de `ONCOLOGY_PRIMITIVES_EDGES` ni un contrato de
  actualización biológica válido en las rutas inspeccionadas. La regla de umbral
  uniforme del simulador y las correlaciones de la CLI no resuelven esa carencia.
  No se transformó prosa ni nombres de fármacos en relaciones causales.
- Al iniciar esta tarea, cambios locales ajenos en
  [pyproject.toml](../../pyproject.toml) ya excluían del wheel el glosario,
  `cli/onco_transducer.py` y `genomics`, y retiraban `babylon60-onco`. Se
  conservaron. Quedaban los dos subcomandos que importaban el módulo excluido
  y la copia completa de esos experimentos al ZIP de lanzamiento.

## Cambio y comprobación inicial en el árbol local

Se retiraron el handler y los dos subcomandos del dispatcher. El
[empaquetador](../../scripts/package_release.sh) excluye ahora esos mismos
componentes oncológicos del ZIP. Las fuentes experimentales permanecen en el
repositorio para consulta; esta retirada no las certifica ni repara su biología.
El extra histórico `onco` se conserva para no modificar dependencias/lockfiles.

La [regresión](../../tests/test_onco_distribution.py) reproduce el anuncio previo
de `onco` en la ayuda y pasa tras retirarlo. Comprueba ayuda, rechazo de ambos
comandos y contenido del ZIP real. Comandos de aceptación:

```sh
uv run --locked pytest tests/test_onco_distribution.py -q
uv run --locked ruff check 01_KISH_ENGINE/babylon60/cli/main_dispatcher.py tests/test_onco_distribution.py
bash -n scripts/package_release.sh
uv build --wheel --out-dir /tmp/babylon60-onco-review-wheel-20261024
```

Resultado: cuatro casos pasan, Ruff y sintaxis shell pasan, wheel construido.
Se inspeccionó su ZIP: sin los tres componentes ni `babylon60-onco` en sus
entry points. Se extrajo en un directorio temporal y se ejecutó el dispatcher
con Python `-I`, importando desde el artefacto extraído: ayuda con salida 0,
ambos comandos retirados con salida 2 y sin traceback. La comprobación usa las
dependencias del entorno; no afirma una instalación desde cero ni ejecución
clínica. No se hizo commit ni publicación.

También pasan las dos pruebas existentes dirigidas de distribución y alcance
del wheel (seis casos dirigidos en total), los controles semánticos locales,
presupuesto y topología, y los enlaces de este informe. Se omitieron las reglas
globales y la telemetría de conversaciones conforme al alcance `--workspace-only`
y `--skip-ghost-listeners`. `git diff --check` global detectó espacios sobrantes
en cambios ajenos de `WHY_BABYLON_60.md`, `src/capability.rs`,
`tests/admission_capability_test.rs` y `tests/test_release_verification.py`;
se conservaron sin tocar.

## Corrección de autonomía del commit

El commit `2ae91d845e` aisló los cambios propios, pero dejó fuera las exclusiones
oncológicas de `pyproject.toml` porque ya estaban en el árbol local. La primera
verificación del wheel dependía de ese estado local y no demostraba que el
commit completara la retirada por sí solo.

Se exportó exclusivamente `git archive 2ae91d845e` a un directorio temporal y se
construyó su wheel. El artefacto todavía contenía `oncology_primitives.py`,
`cli/onco_transducer.py`, seis archivos de `genomics` y el entry point
`babylon60-onco`. La nueva prueba de wheel falla sobre esa exportación sin
corregir, al encontrar el glosario.

La corrección incorpora únicamente la retirada de `babylon60-onco` y las tres
exclusiones oncológicas al `pyproject.toml` versionado. No incorpora la nueva
descripción comercial ni la exclusión de voz presentes en el árbol local;
conserva dependencias y lockfiles. Las fuentes experimentales siguen disponibles
en el repositorio, fuera de la distribución instalada.

Con ese cambio mínimo aplicado a la exportación limpia, pasan los cinco casos
de `tests/test_onco_distribution.py`: ayuda y rechazo de comandos, ZIP real y
wheel real. La prueba del wheel comprueba los módulos y entry points y ejecuta
la CLI desde su contenido extraído con Python `-I`. Se usa el intérprete de
pruebas del entorno para las dependencias; no se certifica una instalación sin
dependencias previas. La construcción del wheel usa el backend aislado de `uv`.

Esta comprobación no requiere los cambios ajenos de `pyproject.toml` ni los
otros archivos modificados del workspace. El fallo del commit original queda
registrado; la corrección se conserva como cambio posterior, sin reescribirlo
ni publicar.

## Iteración del instalador — 26 de octubre de 2026

La revisión del estado versionado `0ea2f5e08e` encontró otra vía de acceso:
`install.sh` utilizaba `uv sync --locked --no-dev`, que instala el proyecto en
modo editable. En una exportación limpia de ese commit, la instalación terminó
con salida 0, pero el Python de la nueva `.venv`, ejecutado desde fuera de las
fuentes con `-I`, seguía encontrando los tres componentes excluidos del wheel.

Se añade `--no-editable` a la instalación Bash y a su vista previa, como ya hacía
el instalador PowerShell. Este comportamiento está descrito en la
[documentación oficial de uv](https://docs.astral.sh/uv/concepts/projects/sync/#editable-installation).
No se modifican dependencias, extras ni lockfiles. Las expectativas de los tests
existentes del instalador se actualizan para reflejar el nuevo argumento.

La nueva regresión copia las fuentes, conserva explícitamente los experimentos,
ejecuta el instalador real en una `.venv` nueva y comprueba desde un directorio
externo que `find_spec()` no encuentra el glosario, `genomics` ni el transductor.
También ejecuta el comando instalado: ayuda con salida 0 y los dos comandos
retirados con salida 2, sin traceback. La regresión falló antes del cambio con
los tres módulos presentes. El lockfile de la instalación se compara byte a byte.

```sh
BABYLON_TEST_INSTALL_BUNDLE=1 uv run --locked pytest tests/test_onco_distribution.py tests/test_first_use_installers.py tests/test_terminal_distribution.py -q
uv run --locked ruff check tests/test_onco_distribution.py tests/test_first_use_installers.py
bash -n install.sh
```

Resultado: 24 pruebas pasan y tres casos de PowerShell se omiten por falta del
intérprete en este equipo; Ruff y la sintaxis Bash pasan. La integración real
de instalación se activa con `BABYLON_TEST_INSTALL_BUNDLE=1`, igual que la
integración existente del ZIP. Sin esa variable se omite para evitar instalar
dependencias en los tests ordinarios. Todos los entornos creados son temporales;
no se alteran ajustes globales del operador ni se realiza activación de Codex.

Se repitieron los 24 casos sobre una exportación limpia de `HEAD` con únicamente
el diff de esta iteración, usando `uv run --locked --extra dev`; se obtuvo el
mismo resultado. También pasan los enlaces del informe y los controles locales
semánticos, de presupuesto y de topología. El alcance `--workspace-only` omite
reglas globales; `--skip-ghost-listeners` omite telemetría de conversaciones.

La comprobación adicional de sdist a wheel en una exportación limpia conserva
las fuentes experimentales en el tar.gz, pero no las incorpora al wheel
reconstruido. No se ha reproducido otro fallo de retirada en esa ruta.

## Reinstalación sobre una `.venv` editable existente

La regresión del instalador cubre ahora dos estados: entorno nuevo y entorno
editable existente. Para el segundo, se registra el antiguo entry point
`babylon60-onco` en el `pyproject.toml` de la copia temporal y se ejecuta una
instalación real con `uv sync --locked --no-dev`, manteniendo la misma versión
y las mismas dependencias. Antes de actualizar se comprueba que la distribución
declara `editable=true`, que los tres módulos son importables y que tanto el
ejecutable antiguo como su entry point existen. No se simula un archivo huérfano.

Se restablece el `pyproject.toml` actual y se ejecuta `install.sh` sobre esa
misma `.venv`. Desde fuera de las fuentes, el Python instalado con `-I` confirma
los tres módulos ausentes, `editable=false` y ningún entry point oncológico.
También se verifica que desaparece `.venv/bin/babylon60-onco`. Se repite el
instalador sobre el entorno migrado y se exige el mismo resultado. El lockfile
permanece idéntico después de cada ejecución; la CLI instalada sigue operativa.

El instalador actual ya supera esta migración; no se añaden borrados manuales
ni opciones de reinstalación forzada. El cambio de esta revisión amplía la
regresión y su evidencia. La prueba falla con el instalador anterior a
`b93324c147`, que conserva los módulos mediante instalación editable, y pasa
con el instalador actual.

Se validó en una exportación limpia del estado versionado con únicamente la
prueba ampliada: 25 casos pasan y tres de PowerShell se omiten por falta del
intérprete. Se usó el mismo comando de integración anterior con
`uv run --locked --extra dev`. Pasan Ruff, los enlaces del informe y los controles
locales semánticos, de presupuesto y de topología; se mantiene la omisión de
reglas globales y telemetría declarada anteriormente. No hay cambios de runtime,
dependencias ni lockfiles en esta revisión.

## Actualización desde un wheel antiguo con la misma versión

La regresión incluye dos procedencias de wheel legado: archivo `.whl` instalado
con `uv pip install`, y wheel construido e instalado con `uv sync --no-editable`
desde el mismo directorio que después se actualiza. En las copias temporales se
restaura el entry point oncológico y se retiran únicamente las tres exclusiones
oncológicas para construir el artefacto antiguo. No se altera la versión ni las
dependencias. La instalación desde archivo usa las dependencias del lockfile y
`--no-deps` para el wheel, sin resolver otras versiones.

Antes de actualizar se comprueban los tres módulos importables, el ejecutable
real y su entry point registrado, y que la instalación no es editable. Después
de restablecer el empaquetado actual, el instalador retira los tres módulos y
el ejecutable, deja vacío el entry point oncológico y conserva exactamente la
versión instalada. Ambas variantes repiten la reinstalación y comparan el
lockfile byte a byte en cada paso. La CLI actual conserva su ayuda y rechaza los
comandos retirados sin traceback.

Con `uv 0.12.0` en este equipo, el instalador actual supera ambas migraciones;
no se ha observado necesidad de forzar la reinstalación ni borrar archivos a
mano. Esta revisión amplía únicamente las pruebas y el informe. La ejecución
en una exportación limpia, con la nueva prueba como único cambio de código,
produce 27 casos aprobados y tres casos de PowerShell omitidos por falta del
intérprete. No se modifican instaladores, dependencias ni lockfiles, ni se
incluyen cambios ajenos.

## Preparación de la verificación nativa de PowerShell en Windows

La prueba de migraciones se omitía explícitamente en Windows y el workflow
`windows-terminal.yml` no la seleccionaba. Se corrige esa falta de cobertura:
la prueba copia también `install.ps1`, elige PowerShell en Windows y utiliza
`.venv/Scripts/python.exe`, `babylon60.exe` y `babylon60-onco.exe`. Mantiene los
cuatro estados iniciales (nuevo, editable, wheel desde archivo y wheel desde
las mismas fuentes), las dos reinstalaciones de cada legado, las comprobaciones
de módulos y metadatos y la conservación de versión y lockfile. Las salidas se
decodifican como UTF-8 y el intérprete de cada entorno temporal se fija al de la
matriz de pruebas.

El workflow Windows existente activa la integración y ejecuta estos cuatro casos
con Python 3.11 y 3.12. Conserva el JUnit junto a la evidencia existente de
revisión, entorno e instalador. La preparación del legado parte de las fuentes
del checkout; el ZIP de distribución ya no contiene los módulos antiguos.

La ejecución nativa de estas nuevas migraciones queda **NO_VERIFICADA**: este
equipo es macOS, no dispone de PowerShell y no hay un host Windows accesible,
según confirmó el operador. No se hace push ni se lanza una ejecución remota de
otra revisión como sustituto. Una ejecución futura del workflow sobre el commit
correspondiente deberá confirmar la desaparición real del `.exe`; el soporte de
la prueba y una comprobación de sintaxis no acreditan ese resultado.

La aceptación local cubre la sintaxis del workflow mediante `actionlint`, Ruff,
los controles documentales y la ejecución de las migraciones Bash en una
exportación limpia. No se modifica `install.ps1` sin un fallo observado en él;
esta revisión se limita a pruebas, selección de CI e informe.

Resultado local: 27 casos aprobados y tres casos de PowerShell omitidos por
falta del intérprete; `actionlint`, Ruff y controles locales pasan. Estos
resultados corresponden a macOS y no se presentan como resultados de Windows.

## Rechazo de migraciones omitidas y conservación de evidencia

Se reprodujo el problema de cobertura: pytest devuelve salida 0 cuando los
cuatro casos se omiten, aunque el JUnit contiene cuatro nodos `skipped`. La
subida de un XML por sí sola no impide que el workflow quede verde en ese estado.

El workflow separa ahora las migraciones en su propio JUnit y utiliza
`--maxfail=0` para intentar todos los casos. El nuevo
[verificador](../../scripts/guards/verify_windows_migrations.py) exige exactamente
los cuatro casos, sin ausencias, duplicados, casos desconocidos, skips, fallos
ni errores de preparación. También exige un JSON completo por caso. Un archivo
ausente, malformado, iniciado pero incompleto o perteneciente a otra revisión,
ejecución, versión de Python, plataforma o instalador produce salida 1.

Cada JSON se actualiza durante la prueba y conserva comandos, códigos de salida,
stdout/stderr y observaciones de los estados anterior y posterior. Incluye la
eliminación del ejecutable y sus metadatos, la versión y la conservación del
lockfile. Solo se marca como aprobado después de todas las comprobaciones de la
CLI. Un error al iniciar un proceso o un timeout conserva el registro parcial y
no acredita finalización. No se almacena el entorno completo ni credenciales.

La ejecución de migraciones, el verificador y la subida de artefactos usan
`if: always()`, sin ocultar errores con `continue-on-error`. El artefacto Windows
de cada Python conserva el JUnit específico, los cuatro JSON disponibles y el
veredicto agregado, además de la evidencia previa del entorno. El verificador
comprueba cada archivo individual; no depende de que `upload-artifact` detecte
ausencias parciales.

Las pruebas del verificador usan fixtures sintéticos para ejercitar 27 clases
de defecto, junto a informes reales de pytest con todos los casos omitidos y
selección incompleta. También comprueban que se conserva la salida de procesos
fallidos y la salida parcial de un timeout. En una exportación limpia pasan
60 casos y se omiten tres de PowerShell; Ruff, `actionlint` y controles locales
pasan. El verificador rechaza el JUnit real de cuatro skips que pytest había
considerado exitoso. El registro por caso también se ha ejercitado en las
migraciones Bash, conservando explícitamente `platform=darwin`.

Esto verifica localmente el rechazo de informes incompletos y la conservación
de evidencia. La migración nativa en Windows y la ejecución de este workflow
sobre el commit final siguen **NO_VERIFICADAS**; no se hace push ni se atribuyen
a Windows las ejecuciones realizadas en macOS.
