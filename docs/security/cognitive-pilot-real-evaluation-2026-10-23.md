# Cognitive pilot: evaluación real del 23 de octubre de 2026

## Contrato y alcance

Se compara la instrucción A/B fijada por `cognitive_pilot`, usando el mismo modelo,
proveedor, límites y frontera de ejecución en ambos brazos. No se compara un
cliente completo sin Babylon con otro instalado, ni se atribuyen cambios a los
pesos. El banco contiene doce familias y cinco etapas: calidad, retención,
transferencia, activación y exploración. Una repetición planifica 120 ejecuciones.

La retención usa una nota acotada en contexto nuevo; no es un seguimiento de
30 días. La transferencia usa nuevos casos de la misma familia. Los jueces IA
reciben paquetes sin marca de condición, con contexto nuevo; tres identidades
del mismo modelo no son tres humanos ni tres modelos con errores independientes.
El estilo del código aún puede revelar la condición.

Los artefactos y recibos se conservan fuera de fuentes en
`~/.babylon60/validation/cognitive-pilot-20261023/`, con planes, reclamaciones
exclusivas, digests, consumo declarado por proveedor y fallos sin reintentos
silenciosos. No se guardan trazas de razonamiento, cabeceras ni credenciales.
Los hashes de código identifican fuentes; no constituyen atestación hardware.

## Gemini: cohorte interrumpida

Modelo explícito `gemini-3.1-flash-lite`, endpoint HTTPS de compatibilidad,
`reasoning_effort=minimal`, temperatura 0,3, máximo 6000 tokens y dos llamadas
por ejecución, plazo 240 segundos, paralelismo dos y cap total 720000 tokens.
Los jueces se fijaron antes de la primera reclamación: tres identidades IA,
una llamada por juicio y cap 432000 tokens. Sin fallback dentro de la cohorte.

- Fuente: `6c8cced100c6c1017f5f231229d1be8577dde55b`.
- Semilla: `20261023`, una repetición, directorio `study/`.
- Plan: `20155c3b26d7d45315b5dfeb7187319f4390a78772c956ad27970b3c2b50bd99`.
- Juicios registrados: `4aa9dcc198379a7d256d008bc5f1dcbffa17fb6fe1b227f05a931bc29abcc325`.
- Resultado: siete ejecuciones completas y una bloqueada por HTTP 503;
  5179 tokens declarados. Se detuvo el despacho, sin reanudar ni sustituir registros.
- No se ejecutaron jueces ni se obtuvo evidencia suficiente de eficacia.

La prueba de humo previa, `smoke/`, conserva dos intentos separados: uno bloqueado
por el antiguo timeout de lectura de 60 segundos y otro completo con 695 tokens,
calidad oculta 100 y backend real `macos-seatbelt`. La corrección del timeout y
los diagnósticos seguros quedaron en AX-168 antes del registro de `study/`.
Una ejecución correcta de humo no demuestra mejora A/B.

## Ollama V2: prueba de humo fallida

Fuente `e0c89a5bf0e1629f7ff968df8501bdebfc7973d8`, semilla `271828`,
directorio independiente `smoke-ollama-v2/`, plan
`05bf8e81e6a20500c08f20b375d8e687329dfbed4d4ca7919998bd27c11f26ef`.
Se usó Qwen3 1.7B Q4_K_M instalado localmente, Ollama 0.32.14,
`think=false`, JSON, contexto 8192, máximo de generación 2048 y ejecución serial.
Ambos intentos produjeron JSON que no cumplía el contrato de acción; se registraron
como fallidos, con 1110 tokens en total. No hubo candidato admitido ni prueba de
mejora. Los registros permanecen intactos.

El alias temporal propio apunta al manifiesto
`8f68893c685c3ddff2aa3fffce2aa60a30bb2da65ca488b61fff134a4d1730e7`.
Se comprueba alias y digest antes de cada inferencia. La copia del alias no
requiere descargar pesos. El modelo de 9B instalado no se utiliza.

## Continuación estructurada

Fuente `287c3d2dc097604b4121742c03ecf4522fd9555f`, backend separado
`ollama_structured_v3`: esquema JSON fijado por rol, comprobaciones semánticas
adicionales y políticas V1/V2 conservadas. `COMMON`, `CONDITIONS`, banco y rúbrica
no cambian. El esquema se aplica de forma idéntica a ambos brazos.

Prueba de humo `smoke-ollama-v3/`, semilla `271829`, plan
`794c2d076eb63dd0045c35cd403f3826676c6687f7529c911d8cd977ad5ddc28`:
un intento completo, dos llamadas, 1159 tokens, 17,36 s, calidad 3,70 %,
backend real `macos-seatbelt`; el otro falló por artefacto JSON inválido,
2472 tokens y 33,38 s. La aceptación del esquema no asegura que el modelo termine
ni resuelva la tarea. No se ampliaron límites después de estos resultados.

Cohorte nueva `study-ollama-v3/`, semilla `20261024`, una repetición,
120 ejecuciones previstas, cap 720000 tokens y paralelismo uno. Cada intento
permite 6000 tokens, dos llamadas, 240 segundos y nota de hasta 8192 bytes;
la temperatura es 0,3. Jueces: tres contextos nuevos del mismo Qwen,
una llamada por juicio, hasta 6000 tokens y 240 segundos, cap 432000 tokens.
Ambos registros preceden a las reclamaciones de la cohorte:

- Plan: `fca495438a38e9fbec6d586821986fd9361bb380d4f6fe7d4660abe1b5cf6607`.
- Juicios: `8770f0bfd279b28339284f9f22e3704297ad1033b408c3952ed0213b3e53a09b`.
- `provenance.json` conserva el commit y BLAKE3 de las nueve fuentes del piloto;
  los recibos se vinculan al plan mediante digest.

El ejecutor terminó con salida 0 por `no eligible runs`: **113 intentos**, de
los que **71 completan el contrato y 42 fallan**, cero bloqueos y 145471 tokens
reportados por Ollama. Los fallos son 26 por agotar las dos llamadas sin entrega
final y 16 por artefacto JSON inválido. Siete retenciones quedaron sin ejecutar
porque su ejecución `quality` dependiente tenía estado `failed`. No se reintentó
ninguno de esos registros ni se modificaron los límites.

Se generaron 13 paquetes anónimos a partir de las exploraciones completas;
corresponden a 39 juicios posibles. Las exploraciones fallidas no se convierten
en paquetes adicionales para completar artificialmente los 72 juicios máximos.

**Los 39 juicios completan el contrato**, con 28661 tokens adicionales y cero
jobs elegibles restantes. No son 39 respuestas humanas ni modelos distintos.
El informe final valida los recibos y conserva seis pares de retención pendientes.
La mediana de activación requerida por el índice no resulta estimable.

Los efectos descriptivos B−A del banco, incluyendo los intentos fallidos con
calidad cero, son:

| Dominio | Calidad, puntos porcentuales | Transferencia, puntos porcentuales | Mecanismos aceptados | Originalidad, escala 0–4 |
| --- | --- | --- | --- | --- |
| Conocimiento | +11,11 | −3,09 | 0 | 0 |
| Creatividad | 0 | 0 | −0,50 | −0,33 |

En la etapa primaria `quality`, las medias de las doce familias son 13,89 % en A
y 19,44 % en B; la exactitud absoluta es baja. En todo el estudio, A tiene
41 recibos completos, 17 fallidos y 2 ausentes; B, 30 completos, 25 fallidos y
5 ausentes. Completar el contrato no equivale a resolver correctamente la tarea.

La cobertura ponderada del índice es 0,75 en conocimiento y 0,80 en creatividad.
No hay puntuación final ni bootstrap completo: ambos son `null`/cero muestras
completas. Las cotas por datos ausentes son [168, 417] y [1, 201], respectivamente;
son cotas del índice registrado, no intervalos de confianza ni una medida de
inteligencia. Los datos no respaldan el umbral 900 de ese índice.

El estado literal de ambos dominios es `critical_or_harmful`, por una bandera
crítica global del juez IA 3 en `packing.0.exploration.A`. Los otros dos jueces
no marcaron esa bandera. Su evidencia cita errores de sintaxis, sin señalar I/O
ni autoridad. La inspección posterior encuentra cinco candidatos idénticos,
`def solve(p):`, rechazados por el parser antes de ejecución y puntuados 0/27;
no contienen I/O ni autoridad y no hay efecto físico observado. Esa bandera
no demuestra una brecha del sandbox y parece exceder la rúbrica de criticidad.
Se conservan juicio, discrepancia e informe sin corregirlos después de ver los
resultados. Una revisión independiente con otro modelo o humana sigue pendiente.

**Conclusión:** evaluación real ejecutada, con tasa alta de fallos y métricas
incompletas; no certifica mejora general ni el objetivo del índice. El +11,11
observado en calidad de conocimiento es un descriptivo de seis familias bajo
este modelo y estos límites, no una ganancia general demostrada.

Una ejecución `quality` con estado `failed` impide su retención dependiente;
una exploración con ese estado no
produce paquete de jueces. Una calidad baja o cero en un recibo `complete`
sí conserva la elegibilidad de la retención. Por ello 120 ejecuciones y 72 juicios son el máximo
planificado, no un número de éxitos garantizados. Un juicio inválido queda como
fallido sin sustituirse. El bloqueo de proveedor o aislamiento detiene el despacho;
las ausencias se reflejan en cobertura y estado pendiente del informe.

## Verificación de implementación y limpieza

La revisión V3 pasó 163 tests, con una omisión y un fallo esperado; `make check`
pasa Ruff/formato y mypy estricto. Linux pasó además el delta de 141 casos,
con sus tres omisiones exclusivas de Seatbelt. Estas verificaciones son distintas
de la eficacia del modelo. Los lockfiles permanecen idénticos y la comprobación
`uv lock --check` / `cargo check -q --workspace --locked` pasó en copia limpia.

Se descargó de memoria y eliminó exclusivamente el alias temporal propio tras
los juicios. `qwen3:1.7b` conserva etiqueta y digest; no se descargaron pesos ni
se usó el modelo de 9B. El recibo `ollama-cleanup.json` registra la comprobación.
El daemon Ollama que ya existía permanece. Para repetir debe registrarse una
cohorte nueva, recreando un alias ligado al manifiesto; no sobrescribir recibos.

## Evidencia local conservada

El [paquete local de evidencia](/Users/borjafernandezangulo/.babylon60/validation/cognitive-pilot-20261023/cognitive-pilot-evidence-20261023.tar.gz)
conserva las cohortes separadas, pruebas de humo, registros, fuentes generadas,
paquetes ciegos, juicios originales, auditoría independiente y recibo de limpieza.
No contiene credenciales ni pesos del modelo y no se ha publicado.

SHA-256: `9a6bc6a5133dea580dbda4262a4d1835ff220e685c9f675ef3696e352b2addd6`.

## Interpretación

Las pruebas unitarias y el encuadre de transporte comprueban implementación;
no sustituyen al estudio real. Los fallos de formato y las observaciones ausentes
se conservan. No se completan con valores inventados ni se mezclan cohortes con
modelos, protocolos o semillas diferentes. El índice recorta pérdidas y debe
leerse junto a efectos con signo, alertas de daño, cobertura y bootstrap por familia.
Un resultado negativo, incompleto o inconcluso no autoriza afirmar mejora general.

La inferencia serial se ejecutó en el M3 Pro de 18 GiB, compartido durante parte
del estudio con validación Linux y compilación de comprobación. El orden se fijó
por semilla, pero esto no aísla el efecto de la carga del host sobre activación.
Los contextos son nuevos; la caché interna de Ollama y los pesos pueden permanecer
calientes según `keep_alive=5m`. Las latencias no son un benchmark de máquina
reservada ni una medida energética. El modelo pequeño cuantizado tampoco
representa a otros tamaños, proveedores o modelos de frontera.

No se ha desplegado producto.
