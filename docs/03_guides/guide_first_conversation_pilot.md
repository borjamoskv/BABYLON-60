# Piloto de la primera conversación

Este piloto compara una instalación activa de Babylon con una referencia sin Babylon en
Codex. Evalúa resultados útiles y verificables; la firma, el Panel, la longitud y el índice
léxico no puntúan. Véanse el [criterio de producto](../../.babylon60rules#modelo-y-presentación)
y el [contrato de presentación](../../01_KISH_ENGINE/babylon60/presentation.md#experiencia-desde-la-primera-respuesta).

El [runner](../../scripts/c5_quality_gates/experience_pilot.py) prepara entradas, importa
evidencia, crea parejas sin etiquetas de condición y calcula el criterio de aceptación.
No invoca modelos, no autentica sesiones y no sustituye a los revisores humanos.
Requiere Python >=3.11 y `blake3`, ya incluido en las dependencias bloqueadas del proyecto.

## Preparación y condiciones

Desde la raíz del proyecto, elegir una carpeta nueva fuera del repositorio:

```sh
uv run --locked python scripts/c5_quality_gates/experience_pilot.py prepare /tmp/babylon60-first-conversation-pilot --seed 20261023
```

La preparación genera 20 ejecuciones: cinco tareas, dos repeticiones y dos condiciones.
`manifest.json` fija un orden aleatorio reproducible. Cada tarea contiene prompts, archivos
de entrada y requisitos esenciales, congelados mediante BLAKE3. Cambiar cualquiera de
ellos invalida el piloto. No se reemplazan resultados importados ni paquetes de evaluación.
Una nueva campaña requiere otra carpeta. Se permite `target/<campaña>` como almacenamiento,
pero **los espacios de ejecución deben copiarse fuera de cualquier repositorio con instrucciones
de agentes**, para que la referencia no herede las pautas del propio proyecto.

Las tareas son: síntesis con evidencia numerada; decisión con coste, residencia y exportación;
consulta de dos versiones de un manual local; corrección de Python con `unittest`; y agenda
en dos turnos con una corrección explícita. Los datos son fixtures de evaluación, no observaciones
de runtime. Cada ejecución usa su propia copia de los archivos y una conversación nueva.

Usar el mismo ejecutable y versión de Codex, modelo y esfuerzo expuestos, permisos, acceso a
herramientas y entorno de trabajo en ambas condiciones. Las diferencias de versión de cliente,
modelo o esfuerzo invalidan la comparación; si el cliente no expone modelo/esfuerzo, registrar
`null` en ambas condiciones y conservar esa limitación en el informe. No inferir el modelo
activo del selector configurado.

- **Control:** `CODEX_HOME` dedicado, sin registro MCP ni bloque global de Babylon y sin
  instrucciones Babylon heredadas por el directorio de trabajo.
- **Babylon:** otro `CODEX_HOME` dedicado, con el paquete instalado y
  `babylon60 setup --client codex`; comprobar `babylon60 doctor --client codex --json`.
  Registrar versión del paquete y el diagnóstico real.
- Conservar evidencia de ambos entornos efectivos, sin credenciales, tokens ni archivos de
  autenticación. Autenticar cada entorno mediante el flujo habitual de Codex cuando proceda.
- Seguir `execution_order`; abrir una conversación nueva para cada ejecución, sin copiar
  pautas manualmente. En continuidad, enviar el segundo prompt dentro de la misma conversación
  inmediatamente después de la primera respuesta. No reutilizar resultados entre repeticiones.

La activación y la entrega del contrato son comprobaciones técnicas. Que una conversación
aplique las pautas exige inspeccionar sus resultados; el diagnóstico no lo certifica.

## Captura e importación

En `runs/<run_id>/result.template.json` está el esquema exacto. Copiarlo a una carpeta de
captura de esa ejecución como `result.json`, completar los datos observados y colocar junto
a él los archivos referenciados con rutas relativas. Se rechazan claves desconocidas,
rutas absolutas, escapes mediante `..`, enlaces fuera de la carpeta y métricas no finitas.

Cada turno incluye `final_file`, `captures` y `artifacts`. Guardar únicamente la respuesta final
en UTF-8, capturas del resultado visible y los entregables relevantes, por ejemplo el código
corregido. **No exportar razonamiento interno, canales de análisis, registros con deliberaciones
ni conversaciones completas.** El esquema excluye campos de razonamiento; el operador debe
revisar también el contenido de los adjuntos antes de importarlos.

Completar versión de cliente, versión de Babylon cuando corresponda, modelo y esfuerzo
cuando estén expuestos. Los booleanos `new_conversation`, `instructions_copied_manually` y
`condition_verified` registran hechos que los revisores deben contrastar con la captura.

Métricas, con el mismo procedimiento en ambas condiciones:

- `time_to_acceptable_seconds`: segundos desde el envío del primer prompt hasta el resultado
  aceptable, incluidas verificaciones y correcciones necesarias. Registrar inicio, fin y
  cronometraje real. No descontar a posteriori esperas desfavorables; si no se llega a un
  resultado aceptable, usar `null` y dejar pendiente ese criterio.
- `corrections`: número de peticiones adicionales necesarias para corregir incumplimientos.
  El segundo prompt predefinido de continuidad no cuenta como corrección adicional.
- `rework`: número de entregas rechazadas que hubo que rehacer tras comprobarlas. Un ajuste
  puede contar también como corrección; aplicar esa definición igual en ambas condiciones.

Adjuntar al menos una evidencia de cada tipo `session`, `timing`, `verification`,
`corrections` y `rework`, cada una con `path`, `kind` y `description`. Un registro explícito
de cero incidencias también debe tener soporte verificable. Para código, adjuntar la salida
real de `python -m unittest -v`; para otras tareas, el registro de contraste de los requisitos
locales. Una cifra escrita por el modelo no constituye prueba de ejecución o cronometraje.

```sh
uv run --locked python scripts/c5_quality_gates/experience_pilot.py import-result /tmp/babylon60-first-conversation-pilot /ruta/captura/result.json
```

La importación copia evidencia y conserva recibos BLAKE3. Los recibos detectan cambios
posteriores respecto de la copia importada; no prueban autenticidad ni integridad frente a
un administrador capaz de sustituir también los recibos. Repetir para las 20 ejecuciones.

## Evaluación de las parejas

```sh
uv run --locked python scripts/c5_quality_gates/experience_pilot.py blind /tmp/babylon60-first-conversation-pilot
```

Sin las 20 respuestas, devuelve `pending` y enumera lo que falta. Con todas ellas, crea
`blind/pairs`: tarea, respuestas A/B por turno y artefactos con nombres neutros. Asigna A/B
aleatoriamente con semilla reproducible y oculta el mapeo en `private/blind_map.json`.
Elimina exclusivamente líneas de firma portable reconocidas por su etiqueta entre corchetes;
conserva los demás bytes y el formato de las respuestas. No borra menciones sustantivas a
Babylon ni reescribe entregables. `private/redactions.json` registra exactamente las líneas
retiradas y digests anterior/posterior. El estilo, el contenido y los artefactos pueden revelar
la condición: no se promete anonimización perfecta.

Un coordinador conserva `manifest.json`, `results` y `private`; entrega solo las parejas a
un usuario objetivo y un revisor independiente. Cada persona registra por separado su
preferencia A/B/empate y una razón antes de recibir evidencia operativa que pueda revelar
condiciones. Conservar esa decisión inicial con fecha. Después, el coordinador comparte los
adjuntos operativos por alias A/B para que ambos contrasten requisitos y métricas. Las capturas
se conservan en privado porque podrían contener identidad; se inspeccionan en esta segunda fase.
El runner no certifica que esta separación se haya respetado.

Completar las plantillas de `blind/reviews/<pair_id>` y guardarlas con nombres
`target_user.json` e `independent.json`, sin `.template`. Usar identificadores seudónimos
estables de personas distintas y declarar `independent_from_other_reviewers: true` solo
si corresponde. El usuario objetivo debe representar el uso evaluado; el revisor independiente
no puede ser el modelo que produjo las respuestas. Registrar `winner: A`, `B` o `tie`,
razón, cada requisito esencial y recuentos observados de errores graves/verificaciones inventadas.

`evidence_reviewed` debe enumerar exactamente `A:session`, `A:timing`, `A:verification`,
`A:corrections`, `A:rework` y los cinco equivalentes de B. Es una declaración humana de
inspección de los archivos importados, no un mecanismo automático de autenticación.
`metrics_verified` solo es verdadero si esos archivos respaldan los contadores y el tiempo.
Errores graves son afirmaciones o acciones que invalidan la utilidad de la entrega o incumplen
una restricción obligatoria; una verificación inventada afirma ejecutar/observar algo sin soporte.

Cualquier desacuerdo en ganador o evaluación requiere `adjudicator.json` de una tercera
persona distinta, usando la plantilla correspondiente. La adjudicación determina el ganador
y cumplimiento; una observación de error grave o verificación inventada de cualquier revisor
en Babylon se conserva como fallo, aunque el tercero prefiera esa respuesta. Las observaciones
adversas del control también se conservan, sin vetar por sí solas el producto evaluado.

## Informe y aceptación

```sh
uv run --locked python scripts/c5_quality_gates/experience_pilot.py report /tmp/babylon60-first-conversation-pilot
```

El informe JSON también queda en `private/report.json`; `--reviews /ruta/revisiones` permite
leer formularios guardados aparte. Estado pendiente o rechazado devuelve código 1; entradas
inválidas, código 2. Preparación, importación y paquete ciego válidos devuelven código 0.

Se acepta el piloto únicamente con diez parejas evaluadas, al menos ocho victorias Babylon,
todos los requisitos esenciales satisfechos por Babylon, cero errores graves y verificaciones
inventadas en Babylon, ninguna pareja con más correcciones o retrabajo en Babylon, y
mediana del tiempo hasta resultado aceptable de Babylon <=125 % de la referencia. Los revisores
deben confirmar el soporte operativo de las métricas. Un empate no cuenta como victoria.

La falta de respuesta, revisión, tercero necesario, evidencia de sesión nueva/conectada,
verificación de métricas o tiempo aceptable produce `pending`, aunque también existan fallos
ya observados. El informe conserva esos fallos. Sin revisores humanos reales no declarar
mejora demostrada. Un resultado aceptado se limita a estos casos y a las combinaciones de
versiones/modelo/esfuerzo registradas; no certifica todos los clientes ni modifica los pesos
del modelo. No guardar resultados de campaña en fuentes documentales ni inventar jueces
o puntuaciones para completar el informe.
