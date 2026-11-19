# CORTEX: autorización del destinatario en un conector de salida

Fecha: 2026-11-18. Alcance: prueba local con datos sintéticos, corrección optativa
sobre un adaptador HTTP existente y evidencia reproducible. No despliegue.

## Resultado y pregunta investigada

La autorización de lectura y la autorización de exportación son decisiones
distintas. El [handoff fijado por el encargo](https://github.com/borjamoskv/BABYLON-60/blob/6c8944482b8b59ccb94245dd666e4ae1329220b8/HANDOFF.md)
documenta `recorded_before_send_unconfirmed`: un registro previo al envío, no
una confirmación del destinatario. En la inspección inicial de
[`Adapter.read`](../../01_KISH_ENGINE/babylon60/mcp/cortex_memory_mcp.py), el
actor y el proyecto procedían del binding de lectura; esa operación no
autorizaba un proyecto externo receptor.

El adaptador existente
[`post_with_retry`](../../01_KISH_ENGINE/babylon60/transducers/http.py)
no recibe una política de destinatarios. La prueba inicial, ejecutada antes de
añadir el conector, observó entrega tanto a A como a B. También observó entrega
a B por redirección 307 desde A al configurar el cliente con redirecciones
habilitadas. Esto es una carencia respecto al contrato solicitado, no una
demostración de explotación de CORTEX en producción. HTTPX no sigue
redirecciones por defecto; el contraejemplo habilita esa opción expresamente.

Se añadió [`CortexExportConnector`](../../01_KISH_ENGINE/babylon60/transducers/cortex_export.py),
que reutiliza ese adaptador sin cambiar sus otros consumidores. No se instaló
Envoy ni se alteró el transporte MCP. El exportador existente
[`export_facts`](../../01_KISH_ENGINE/babylon60/transducers/export.py) serializa
contenido; no es por sí mismo un transporte con identidad de destinatario.

## Transferencia de Envoy y contrato del conector

Se transfiere la separación entre decisión de autorización y su aplicación
antes del envío. La documentación de
[Envoy ext_authz](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/ext_authz_filter)
advierte que cambiar la ruta después de autorizar puede eludir controles.
No se transfiere una configuración de proxy ni se afirma equivalencia con Envoy.

El anfitrión configura el actor, un resolvedor de destinos, la política y el
destino de auditoría. El llamador selecciona un alias; no proporciona una URL
libre ni sustituye el actor. Cada receptor combina origen del servicio y
proyecto, con la ruta fija `/projects/{project}/records`. HTTPS es obligatorio;
HTTP a loopback exige una opción explícita para ensayos.

El [hook de petición de HTTPX](https://www.python-httpx.org/advanced/event-hooks/)
se ejecuta con el cuerpo ya serializado, antes del transporte. La decisión
vincula actor, identificador del registro, SHA-256 de los bytes reales,
servicio/proyecto, método POST e identificador único de exportación. Debe
coincidir íntegramente, permitir la operación y conservar su vigencia local.
Una autorización vieja no coincide con otra exportación.

Después de consultar la política y registrar la intención, se resuelve de
nuevo el alias y se comprueba la caducidad. Un cambio de receptor aborta el
envío. El transporte conserva la URL y los bytes ya preparados; no consulta
otra vez el alias ni sigue redirecciones. No hereda proxies del entorno y hace
un solo intento, también ante 429 o pérdida de conexión.

La auditoría contiene metadatos, hash y motivos fijos, nunca el cuerpo ni el
texto de las excepciones de política o auditoría. Los identificadores deben
ser opacos: este control no convierte identificadores o hashes en información
pública. Un fallo de auditoría previo al envío lo detiene; uno posterior no
revierte ni niega una entrega ya observada.

## Prueba y resultados

La [suite](../../tests/test_cortex_export_egress.py) abre un servicio HTTP real
en un puerto efímero de loopback, con dos receptores lógicos e inboxes
independientes A/B. Comparten exactamente esquema, host y puerto. El marcador
es sintético y no se lee memoria privada. Los tests del adaptador sin control
son controles positivos de alcance de B; su éxito reproduce la carencia.

Resultado: **43 passed** en 5,44 s; tres casos reproducen el comportamiento
del adaptador genérico y los otros 40 comprueban el conector y sus entradas.
Ruff, formato, tipos, contratos semánticos, presupuesto local y topología
terminaron con código 0. La duración es la de esta ejecución, no un benchmark.

| Caso | Observación verificada en el ensayo |
| --- | --- |
| Agente y registro permitidos a A | A conserva los bytes; el acuse coincide con A, exportación y hash. |
| Mismo agente, registro y servicio hacia B | Ningún receptor recibe; motivo `policy_denied`, sin marcador en auditoría. |
| Aprobar A y cambiar su alias a B | Cero entregas; motivo `recipient_changed`. |
| Cambio de ruta durante auditoría | Cero entregas; la aprobación no se traslada. |
| A devuelve una redirección a B | Solo A recibe; B queda vacío y no se declara confirmación. |
| Decisión caducada, reutilizada o para otro actor/registro/hash/destino | Cero entregas nuevas. |
| Cambiar contenido conservando el identificador del registro | Denegación por la política del ensayo, que conoce el hash permitido. |
| HTTP 200 sin acuse completo o con otro destinatario/hash/exportación | Respuesta recibida, entrega sin confirmar. |
| Error o timeout de autorización | Cero entregas; error redactado. |
| 429 o desconexión después de recibir el cuerpo | Un solo intento; no se presume ausencia de entrega. |

Los estados distinguen `not_dispatched`, `recorded_before_send_unconfirmed`,
`dispatch_attempted_unconfirmed`, `response_received_unconfirmed` y
`delivery_confirmed`. El último exige un acuse con `status="received"`,
`recipient`, `export_id` y `body_sha256` coincidentes. En el ensayo, el inbox
del receptor constituye además un testigo independiente del resultado.

La campaña acotada realiza una pareja A/B de calentamiento y luego 20 parejas
concurrentes: exige 21 recepciones totales en A y ninguna en B. No mide
rendimiento ni acredita resistencia bajo carga de producción.

Comando principal:

```sh
uv run --locked pytest tests/test_cortex_export_egress.py -q
```

La [evidencia de ejecución](evidence/cortex-export-egress-20261118.json)
conserva comandos, códigos de salida, resultados y hashes de las fuentes
ensayadas. Incluye Ruff, comprobación estricta de tipos sobre los dos archivos
nuevos, contratos documentales, presupuesto local y topología. La telemetría
global y los ghost listeners están excluidos. El árbol compartido contiene
trabajo concurrente; esta evidencia no certifica sus otros cambios ni CI remoto.

## Límites e integración pendiente

- Solo este conector aplica el control. No se ha conectado a una salida real
  de CORTEX ni a un servicio externo; el camino completo desde lectura
  autenticada hasta un proyecto real queda `NO_VERIFICADO`.
- La política del ensayo reconoce un actor, registro, hash y proyecto A. Una
  integración debe obtener identidad y contenido de fuentes confiables; no
  autorizar únicamente por un identificador elegido por el agente. El permiso
  de lectura sigue siendo responsabilidad del adaptador de memoria.
- El servicio debe garantizar que la ruta del proyecto corresponde a ese
  receptor. Un acuse HTTP no es una firma ni prueba almacenamiento durable,
  ausencia de reenvío interno o identidad frente a un servicio malicioso. La
  ruta, TLS y el contrato de acuse requieren validación con cada servicio real.
- La auditoría es un callback obligatorio; el ensayo usa una lista local.
  Durabilidad, ledger, firma hardware y recuperación tras caída no se acreditan.
- No hay confinamiento del proceso: quien posee el texto y puede abrir otra
  conexión puede eludir este conector. La conclusión es únicamente que este
  conector no entregó el registro a B en los casos protegidos ensayados.

El ensayo no modificó dependencias ni lockfiles ni ejecutó un despliegue. Su
evidencia no acredita por sí misma commit o push; la publicación se verifica aparte.
