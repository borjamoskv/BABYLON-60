# AgentPager: rechazo de reutilización y despertar unicast — 28/10/2026

## Contrato previo a las ediciones

Resultado: imponer en código la difusión global única de C0279, rechazando
una segunda llamada sin alterar el primer pulso, y reparar el despertar
unicast C0278. El cierre documental anterior es insuficiente y se sustituye
por una corrección ejecutable con regresiones.

Rutas: `scripts/c5_sharur/agent_beeper.py`,
`tests/test_agent_beeper_regressions.py`, registro de la ronda 3 y evidencia de
esta intervención. Preservar el árbol sucio y los dictámenes anteriores.
Aplican los [contratos de concurrencia y evidencia](../03_guides/agent_contracts.md#poc-y-evidencia).

Aceptación: segunda difusión produce `RuntimeError` bajo un bloqueo del pager;
conserva el primer payload; unicast despierta al destinatario ya suspendido;
difusión alcanza a agentes actuales y tardíos; cancelación y baja no dejan
esperas huérfanas. Añadir reproducción previa, regresiones, calentamiento y
ejercicio concurrente en memoria. Sin datos del operador, efectos externos,
cambios de dependencias ni commits. Actualizar el coste del broadcast si cambia.

Después se extraerán únicamente los P1 OPEN con dictamen REPRODUCED para
presentar el Lote 1 agrupado por archivo. Sus módulos no se editarán en esta
intervención.

## Resultado

**C0278 y C0279 corregidos en código y marcados FIXED.** Se conserva el cierre
documental anterior como historia superada; no acredita la corrección actual.

- `_emitted` se comprueba y cambia bajo el RLock del pager. Una segunda
  difusión lanza `RuntimeError` antes de sustituir payload o activar eventos,
  incluso si el segundo payload coincide con el primero.
- Cada receptor espera su evento de destinatario. Unicast activa ese mismo
  evento; la difusión activa los de todos los agentes registrados. Los agentes
  tardíos siguen recibiendo el primer pulso retenido.
- El bucle de recepción revalida el estado tras despertar, consume el unicast
  una vez y suspende sin mantener el bloqueo. La baja despierta las esperas
  antiguas y la identidad del registro impide cruzarlas con un registro nuevo.
- La difusión cuesta O(N + W), con N destinatarios registrados y W esperas
  actuales. No se crean sub-tareas auxiliares para combinar eventos.

La [reproducción previa](evidence/swarm100-pager-20261028/before.log) dio
**11 failed, 3 passed**. Con el parche, las
[14 regresiones](evidence/swarm100-pager-20261028/after.log) pasan. Cubren
rechazo de segunda difusión, unicast ya suspendido y previo, aislamiento entre
destinatarios, agentes tardíos, cancelación, baja/re-registro, dos receptores
del mismo ID y tres rondas de calentamiento más veinte rondas mixtas de
32 receptores.

La [revisión independiente](evidence/swarm100-pager-20261028/independent-review.json)
no encontró fallos accionables dentro del contrato. Ejecutó las 14 regresiones
y once comprobaciones adicionales, incluyendo fanout de 512 destinatarios en
tres rondas de calentamiento y veinte rondas verificadas, carreras programadas
alrededor de la suspensión y ausencia de tareas pendientes. Son pruebas
concurrentes en memoria, no mediciones de rendimiento o aislamiento físico.

[Validación y hashes](evidence/swarm100-pager-20261028/validation.json):
pytest dirigido, Ruff, MyPy, enlaces, controles documentales y registro
reconciliado. Los [cambios de estado por ID](evidence/swarm100-pager-20261028/candidate-status-updates.json)
remiten al hash vigente y a las regresiones.

## Límites y cola siguiente

El pager pertenece a un único event loop y sus llamadas deben hacerse en ese
hilo. El RLock no convierte los eventos asyncio en objetos multihilo. El
buzón unicast sigue teniendo un único slot pendiente por destinatario; envíos
sucesivos sin consumo pueden reemplazarse. No se introduce una garantía FIFO.
Una nueva ronda global requiere una instancia nueva.

Quedan 567 hallazgos únicos OPEN del inventario original (80 P1, 477 P2,
10 P3), tres mitigados y el P1 adicional SW100-R3-0001. El
[Lote 1 propuesto](PLAN_SWARM100_LOTE1_2026-10-28.md) contiene los tres P1
OPEN con reproducción aislada. Sus cuatro archivos productivos conservan los
hashes de selección; únicamente se ha preparado el plan.
