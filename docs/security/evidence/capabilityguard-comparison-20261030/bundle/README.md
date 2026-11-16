# Comparación reproducible de permisos en CapabilityGuard

Este paquete congela una tarea unitaria, su prompt y sus criterios de aceptación.
No contiene una solución. Las copias de `capability_guard.py` y `capabilities.py`
conservan los bytes del working tree identificado en [source-manifest.json](source-manifest.json).
Los dos inicializadores vacíos son soporte del ejercicio, no copias del runtime.

La comparación evalúa configuraciones completas de sesión. No permite atribuir
una diferencia a los pesos del modelo ni generalizarla a otras tareas.

## Contenido y controles

- [PROMPT.txt](PROMPT.txt): texto idéntico para ambos entornos.
- [snapshot](snapshot/AGENTS.md): estado inicial que se materializa en cada intento.
- [Casos](acceptance/cases.json) y [suite congelada](acceptance/test_acceptance.py): contrato externo a la entrega.
- [Entorno](env/pyproject.toml) y [lock](env/uv.lock): Python 3.14.7, pytest y Ruff fijados.
- [Campaña](campaign.json): cinco repeticiones por condición, con orden alternado.
- [Plantilla de métricas](metrics-template.json): valores desconocidos como `null`.
- [Manifiesto](manifest.json): SHA-256 de cada archivo y del snapshot.

Los hashes detectan diferencias respecto de una copia maestra confiable. No son
atestación hardware. Conserva el ZIP y su checksum fuera del alcance de las sesiones
participantes. Los archivos archivados en `context/` registran procedencia documental;
no afirman que se hayan cargado las instrucciones globales de ningún cliente.

## Preparación fuera del tiempo medido

Usa rutas nuevas fuera de `bundle/`. Estos ejemplos suponen que el directorio actual
es este paquete. Sustituye `/tmp/cg-env` por un entorno nuevo si ya existe.

```sh
python3 benchmark.py verify
python3 benchmark.py setup --environment /tmp/cg-env
python3 benchmark.py prepare --destination /tmp/cg-A01
```

`setup` usa `uv sync --locked` con un entorno separado y nunca sobrescribe uno
existente. Puede necesitar descargar Python o dependencias. No usa los lockfiles
ni el entorno virtual del repositorio original. Cada condición debe tener las mismas
versiones fijadas; registra también uv, OS, arquitectura y herramientas observadas.

El operador puede verificar el baseline sin pedir cambios a un agente:

```sh
python3 benchmark.py evaluate --workspace /tmp/cg-A01 --environment /tmp/cg-env --output /tmp/cg-baseline
```

Se espera código de salida `1`: el snapshot aún contiene los fallos. La falta de
tests del participante también se registra; no se confunde con un error del runner.
El código `2` indica un error de integridad, uso, configuración o captura.

Para comprobar el propio evaluador, usa el entorno ya provisionado:

```sh
CG_HARNESS_ENV=/tmp/cg-env UV_PROJECT_ENVIRONMENT=/tmp/cg-env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run --project env --locked --no-sync pytest acceptance/test_harness.py -c env/pyproject.toml --noconftest --import-mode=importlib -p no:cacheprovider -q
```

Estas pruebas usan copias temporales del baseline y la etiqueta `harness_validation`;
no son sesiones de la campaña ni generan una solución.

## Ejecución de una sesión

Abre un chat nuevo sin este historial ni resultados anteriores. Materializa un
workspace nuevo para cada ID de [campaign.json](campaign.json). Entrega exactamente
[PROMPT.txt](PROMPT.txt); no añadas pistas, marcas de proveedor ni soluciones de otras sesiones.

Justo antes de entregar el prompt, inicia el registro:

```sh
python3 benchmark.py start --workspace /tmp/cg-A01 --environment /tmp/cg-env --run /tmp/cg-run-A01 --run-id A01
```

Guarda la correspondencia entre A/B y los entornos fuera del paquete y del material
del revisor. Documenta las instrucciones y permisos inyectados por cada cliente que
sean observables. Igualar el prompt no iguala automáticamente esas instrucciones.

El participante puede probar su trabajo con el mismo entorno bloqueado. Desde su
workspace, usa el path real al paquete para `--project` y `--config`:

```sh
UV_PROJECT_ENVIRONMENT=/tmp/cg-env PYTHONPATH=src uv run --project /ruta/al/bundle/env --locked --no-sync pytest tests -q
UV_PROJECT_ENVIRONMENT=/tmp/cg-env uv run --project /ruta/al/bundle/env --locked --no-sync ruff check --config /ruta/al/bundle/env/pyproject.toml src/babylon60/guards/capability_guard.py tests
```

Al recibir una entrega terminada, sin ediciones concurrentes, ejecuta el evaluador
desde una copia maestra fuera del workspace del participante:

```sh
python3 benchmark.py evaluate --workspace /tmp/cg-A01 --environment /tmp/cg-env --run /tmp/cg-run-A01 --output /tmp/cg-evaluation-A01-1
```

El evaluador congela la entrega, genera `submission.diff` y ejecuta la suite externa,
los tests aportados y Ruff sobre esa copia. Exige el número completo de casos sin
skips, rechaza cambios fuera de alcance y registra cada intento en `events.jsonl`.
Para una nueva entrega usa otro `--output`; no se sobrescriben resultados previos.

## Aceptación y métricas

El contrato contiene 124 combinaciones de permisos, riesgos y entradas inválidas,
más tres comprobaciones de API y alcance. También se requieren tests propios que
pasen sin skips y Ruff limpio. `validate_tool_execution` debe conservar su AST.
La implementación debe seguir permitiendo casos válidos: rechazar todo no supera
la aceptación. [criteria.json](criteria.json) fija las condiciones antes de ejecutar.

La aceptación automática es técnica. La revisión humana sigue pendiente y debe
comprobar alcance, explicaciones y límites sin conocer la condición del parche.
No hay puntuación por longitud de respuesta ni cantidad de comandos. Compara
corrección y regresiones primero; después tiempo observado, coste e intervenciones
con fuente y número de nuevas entregas. No sustituyas datos ausentes por cero.

`start` y `evaluate --run` deben ejecutarse en el mismo host y arranque para que el
reloj monotónico sea comparable. El tiempo incluye esperas del operador y las
evaluaciones anteriores; el tiempo de evaluación se guarda por separado. La
provisión del entorno y la materialización inicial ocurren antes de `start`.

No hay una comparación A/B ejecutada en este paquete. Diez sesiones de una sola
tarea serían un piloto exploratorio; no acreditan una clasificación general.
