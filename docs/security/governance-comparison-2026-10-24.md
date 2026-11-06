# Gobernanza: comparación antes y después del 24 de octubre de 2026

La revisión **no ha demostrado una mejora de calidad ni de retrabajo** en este
banco: ambas versiones resolvieron las diez ejecuciones asignadas sin correcciones
por defectos. La nueva versión empleó un **11,4 % menos de tiempo medio**, pero
fue más rápida en seis de diez pares y su mediana global empeoró. Es una señal
descriptiva de eficiencia en tareas sencillas, insuficiente para afirmar una
mejora general del comportamiento.

## Contrato y versiones

Se ejecutaron cinco tareas del banco existente
[experience_pilot.py](../../scripts/c5_quality_gates/experience_pilot.py), sin
seleccionarlas por sus resultados: síntesis, decisión con restricciones,
consulta documental, corrección de código y continuidad con cambio de requisitos.
Hubo dos repeticiones por tarea y versión: **20 ejecuciones y 24 turnos**.

- **Antes:** `a474d9b2fbaeadd4d9e586a807f07990d8309495`.
- **Después:** `c6dd7337c7a265ee85421fad529f4dafb9961fc1`.
- Se congelaron los ocho documentos centrales y las siete reglas activas de
  cada referencia. Manifiesto y AGENTS suman 10.183 y 9.890 bytes, respectivamente.
- Modelo configurado y devuelto por el servidor: `gpt-6.1-sol`, esfuerzo
  `xhigh`, proveedor `openai`, servicio `priority`; Codex CLI `0.164.0`.
- Ejecución secuencial, semilla `20261024`. Se sorteó el orden inicial de tareas
  y condiciones; la segunda repetición invirtió ambos órdenes. Cada ejecución
  empezó con contexto nuevo; continuidad conservó la misma sesión entre turnos.
- Límite fijado: 300 segundos por turno y, si hubiera un defecto, una corrección
  adicional como máximo. No hubo tiempos agotados, sustituciones de modelo,
  reparaciones ni reintentos de ejecuciones fallidas. Las pruebas de conexión
  previas quedaron fuera de la comparación.

El plan y las rúbricas se guardaron antes de la primera tarea, con SHA-256
`cd6b65da73232f658bcd31c06853099ae710481b2bc2980e5629780c6a5d3f44`.
Este registro local acredita integridad comprobable, no un sellado de tiempo
externo ni atestación hardware.

## Entorno y medición

Cada tarea utilizó una carpeta sintética nueva fuera del repositorio, con sus
entradas completas y las referencias de gobernanza congeladas. Manifiesto y
AGENTS se inyectaron explícitamente; los demás documentos quedaron disponibles
para consulta. Su mera disponibilidad no demuestra que el modelo los aplicara.
No se copiaron el runtime ni los validadores del producto. El contexto común
avisaba de que no era un checkout y de que esas herramientas no estaban disponibles.

Se desactivaron mediante configuración MCP, plugins, descubrimiento de skills
locales, búsqueda web, memoria y hooks de inicio; los comandos tuvieron permiso
de escritura en el workspace y red desactivada. El cliente siguió declarando
`~/.codex/AGENTS.md` como fuente global: se conservó una copia común y se comprobó
su hash antes de cada ejecución. No se presenta el cliente como libre de toda
instrucción base o configuración del anfitrión.

La única adaptación del banco fue sustituir `python -m unittest -v` por
`python3 -m unittest -v` en ambas condiciones, porque el alias `python` no
existía. No se cambiaron entradas, resultados esperados ni rúbricas.

- **Calidad:** cumplimiento binario de los 19 requisitos originales del banco,
  repetidos en cada condición y repetición: 76 comprobaciones. La puntuación de
  una tarea es la proporción de requisitos satisfechos. No mide excelencia
  estilística, creatividad ni capacidad general.
- **Tiempo:** reloj monotónico desde el envío del turno hasta su entrega.
  Continuidad suma los dos turnos previstos. Las respuestas se comprobaron
  después; todas resultaron aceptables. No se incluyen preparación del banco,
  arranque de sesiones ni espera/revisión del evaluador. Por tanto, no es una
  medición completa del tiempo humano hasta aceptar el trabajo.
- **Retrabajo:** una entrega rechazada por defecto y su corrección posterior.
  El cambio previsto de agenda de 90 a 60 minutos es un cambio de requisitos,
  no retrabajo. Los fallos de comandos intermedios se registran por separado.
- **Consumo:** contadores del servidor; se usa el total acumulado de la última
  respuesta de cada sesión, evitando sumar dos veces el primer turno de
  continuidad. No se dispone de un coste monetario atribuible.

Las respuestas se revisaron en paquetes sin etiqueta de condición. La revisión
semántica la realizó la IA de esta conversación: **no hubo evaluadores humanos
ni un juez independiente**. Tampoco fue doble ciego; las salidas de herramientas
pueden revelar qué instrucciones se consultaron. Las comprobaciones ejecutables
del código se realizaron aparte de las declaraciones del modelo.

## Resultados

Los tiempos de esta tabla son medias de las dos repeticiones, en segundos.
Un cambio negativo indica menor duración. Cada fila aprobó 2/2 ejecuciones en
ambas condiciones y tuvo cero reparaciones por defectos.

| Tarea | Antes | Después | Cambio | Aceptación comprobada |
| --- | ---: | ---: | ---: | --- |
| Síntesis | 12,29 | 11,15 | −9,3 % | Cifras, fuentes E1–E4, límites causales y máximo 150 palabras. |
| Decisión | 17,11 | 18,16 | +6,1 % | C por 84 €/mes y 2 h; ninguna opción válida con 60 €. |
| Documentación | 12,41 | 13,56 | +9,3 % | Destino explícito, recibo completo, citas de archivo/sección y ausencia de ejecución del ejemplo. |
| Corrección de código | 35,64 | 26,82 | −24,7 % | Lista vacía devuelve None; medias conservadas y prueba añadida/ejecutada. |
| Continuidad | 28,70 | 24,33 | −15,2 % | Agendas de 90/60 min y 6/4 participantes, dos descansos y prioridades conservadas. |

| Medida agregada | Antes | Después |
| --- | ---: | ---: |
| Requisitos satisfechos | 38/38 | 38/38 |
| Entregas aceptables al primer intento | 10/10 | 10/10 |
| Tiempo medio por ejecución | 21,23 s | 18,80 s |
| Mediana global por ejecución | 17,11 s | 18,16 s |
| Tiempo acumulado de turnos | 212,31 s | 188,05 s |
| Entregas rechazadas / reparaciones | 0 / 0 | 0 / 0 |
| Intervenciones humanas durante las tareas | 0 | 0 |
| Comandos ejecutados | 55 | 49 |
| Comandos con salida distinta de cero | 7 | 5 |
| Tokens de entrada, incluido contexto repetido | 1.076.751 | 994.665 |
| Tokens de entrada recuperados de caché | 859.392 | 825.216 |
| Tokens de salida declarados | 14.272 | 11.527 |
| Palabras en respuestas finales, ambos turnos si procede | 1.536 | 1.447 |

La nueva versión fue más rápida en **6/10 pares**. La mediana de los cocientes
después/antes fue 0,907, diferente de la mediana global de duraciones de la tabla.
La mejora temporal apareció en ambas repeticiones de síntesis y código; decisión
fue más lenta en ambas. Documentación y continuidad cambiaron de signo entre
repeticiones. No se selecciona una sola estadística como prueba de superioridad.

Los comandos con salida distinta de cero **no son siete y cinco soluciones
incorrectas**. Antes hubo cuatro consultas Git fuera de un repositorio, dos
intentos de ejecutar validadores ausentes y una búsqueda en rutas inexistentes.
Después hubo cuatro consultas Git y una búsqueda `rg` sin coincidencias
(`exit 1`, que no implica un error de ejecución). Ninguna prueba de aceptación
del código falló. Persisten comprobaciones innecesarias en ambas condiciones.

Los cuatro artefactos de código son iguales y pasan sus dos tests de unittest.
Además, cada artefacto pasó seis casos del evaluador: vacío, positivos, negativos,
cero, signos mezclados y decimales. Son 24 aserciones adicionales. El tiempo de
esas comprobaciones fue 0,072–0,091 segundos por artefacto y se conserva separado
del tiempo de generación. Los ejemplos `report export` no se ejecutaron.

## Interpretación y límites

La revisión reduce algo de fricción observada y consumo en este ensayo: 11,4 %
menos de tiempo medio, 7,6 % menos de tokens de entrada y 19,2 % menos de salida.
Sin embargo, calidad y retrabajo tienen un **efecto techo**: ambos brazos ya
cumplen todos los requisitos. El resultado no prueba equivalencia ni mejora
general; solo que no se observaron regresiones en estos criterios.

La muestra tiene cinco tareas distintas, no veinte tareas independientes. No se
controlaron caché ni latencia del proveedor; la fracción de entrada recuperada
de caché fue 79,8 % antes y 83,0 % después. Tampoco se midió trabajo prolongado en
un checkout real, validadores instalados, efectos protegidos, atestación, bloqueo
por contexto insuficiente o adopción por otros clientes. El banco no permite
atribuir la mejora temporal exclusivamente a las reglas ni certificar el runtime.

Conservar la revisión por su claridad normativa es compatible con estos datos;
afirmar que mejora realmente calidad y retrabajo todavía no lo es. Una campaña
posterior debería usar tareas con fallos y fricción observados, un checkout
controlado y evaluación humana o independiente, fijando todo antes de ejecutarla.
No se modificaron reglas ni criterios después de ver los resultados de este banco.

La incorporación de este informe y su referencia en la guía pasó 65 regresiones
de gobernanza con `uv run --locked pytest tests/test_governance_gates.py -q`.
También pasaron Ruff sobre los tres scripts del ensayo, los enlaces locales de
ambos documentos, el auditor semántico local, el presupuesto local y la topología
del árbol. El presupuesto omitió explícitamente configuración global y telemetría
del anfitrión. Estos controles verifican documentos y evidencia, no eficacia del LLM.

## Evidencia y reproducción

Los artefactos locales están en
`~/.babylon60/validation/governance-comparison-20261024/`:

- `preregister.json`, su hash y `snapshots/`: plan, rúbricas, orden y documentos.
- `runner.py`: ejecutor de sesiones efímeras. Su hash está en el plan.
- `runs/01.json` a `runs/20.json`: configuración devuelta, comandos/resultados,
  respuestas finales, ficheros entregados, tiempos y uso. Se descartan eventos
  de razonamiento; los contadores numéricos no contienen deliberaciones.
- `review-packets.json`, `reviews.json`, `code-checks.json`: revisión y pruebas.
- `analyze.py`, `results.json`, `verify_evidence.py`, `verification.json`:
  cálculos, controles de integridad y cobertura.
- `SHA256SUMS`: inventario final verificable de los artefactos conservados.

Para recalcular, sin repetir inferencias ni modificar configuración global:

```sh
cd ~/.babylon60/validation/governance-comparison-20261024
shasum -a 256 -c SHA256SUMS
python3 analyze.py summarize
```

`verify_evidence.py` comprueba además las carpetas temporales originales mientras
se conserven. Para repetir la campaña, copiar `runner.py` a un directorio nuevo,
comprobar las referencias Git y ejecutar `freeze` y `run`; revisar las entregas
antes de crear el marcador `finish`. Reutilizar resultados existentes no cuenta
como una repetición nueva. El protocolo del piloto de experiencia original,
con revisión humana, no se declara satisfecho por esta campaña derivada.
