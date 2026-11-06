# Lote 6 ejecutado: selección y transporte — 29/10/2026

C0132 y C0133 pasan a FIXED. La única fuente productiva editada es
`01_KISH_ENGINE/babylon60/kernel/swarm_orchestrator.py`. El
[registro reconciliado](evidence/swarm100-round3-20261028/registry.json)
y la [validación final](evidence/swarm100-lot6-20261029/validation.json)
conservan estados, comandos, hashes y límites.

## Reproducción y evidencia

Las [seis reproducciones previas](evidence/swarm100-lot6-20261029/before-tests.log)
fallaron contra el [hash seleccionado](evidence/swarm100-lot6-20261029/before-source-manifest.json):
selector desconocido, HTTP de proveedor por entorno o configuración explícita
y carga automática de dotenv. El original alcanzó el registrador HTTP en rutas
que debían rechazarse. El entorno era sintético y dotenv estaba bloqueado
antes de importar: no se leyó .env ni credencial real.

**650 pruebas aprobadas y 1 omitida** en la suite relacionada final, con hashes
idénticos antes/después. Incluye **104 regresiones nuevas**, diez pruebas
existentes de rate-limit y los lotes anteriores. El caso dependiente de
strike_rs se omitió con ese módulo bloqueado antes de recoger los tests.
También pasan Ruff, MyPy con check-untyped-defs y los controles documentales.

La [revisión independiente](evidence/swarm100-lot6-20261029/independent-review.json)
repite 114 casos del módulo/rate-limit y añade nueve controles propios: URLs
adversariales, rutas válidas, cinco códigos de redirect, mutación durante retry,
despacho directo, errores y cancelación. Cero intentos de socket. Los positivos
usan HTTPX real con MockTransport; no prueban TLS, DNS ni un proveedor real.

| ID | Corrección | Aceptación observada |
| --- | --- | --- |
| C0132 | Selector exhaustivo sin fallback remoto; defaults inertes y resolución sólo del backend elegido. | Selectores inválidos no leen entorno/credenciales ni construyen cliente. Las cuatro selecciones válidas conservan su ruta; local no lee claves remotas. |
| C0133 | Validación de configuración/cliente/despacho, snapshot por llamada y rechazo de rutas implícitas. | URL explícita o mutada insegura falla antes del transporte. Redirect no produce segundo envío; retries conservan URL/clave/modelo/timeout originales. |

## Contrato de destino y credenciales

El backend predeterminado sigue siendo moonshot remoto. La corrección elimina
el fallback para valores desconocidos; no convierte el default en inferencia
local. La configuración directa y el cliente vuelven a validar antes de usar
el destino. La propiedad .api_key del consumidor conserva su contrato.

Para los hosts externos de proveedor, se exige HTTPS y puerto 443:
api.moonshot.cn para Moonshot y openrouter.ai para OpenRouter. El parser rechaza
userinfo, query/fragment, controles, backslash, puerto inválido, hosts ajenos o
ambigüedad con HTTPX. Los endpoints locales se limitan a localhost, 127.0.0.1 y
::1, con puertos válidos y HTTP/HTTPS; los roles locales nunca envían Bearer.

**Excepción preservada:** la allowlist anterior permitía overrides de un backend
remoto a un gateway loopback explícito. Esa ruta sigue aceptando HTTP/HTTPS y
puede enviar la clave del backend remoto al gateway elegido. Por ello no se
afirma que todo override de un rol remoto use HTTPS. No se amplía la excepción
a otras IP privadas/LAN ni se resuelven nombres para demostrar aislamiento OS.

Cada llamada captura backend, URL, clave, modelo y timeout en una tupla inmutable;
sus reintentos reutilizan ese destino. La siguiente llamada revalida el config
nuevo. Se conservan número de intentos, backoff, Retry-After, circuit breaker y
propagación de cancelación. El [control por AST](evidence/swarm100-lot6-20261029/scope-check.json)
confirma helpers de rate-limit, pager, telemetría y fases no afectadas preservados.

El helper HTTP exige el backend y valida de nuevo antes de construir AsyncClient.
Rechaza Host/proxy headers y Authorization de un rol local. Se fijan
follow_redirects=False y trust_env=False; proxies/CA ambientales ya no son una
ruta implícita. El SDK conserva su verificación TLS normal, sin acreditarla aquí.

## Compatibilidad y límites

- La importación no carga .env ni configura el logger global. El caller puede
  preparar su entorno explícitamente. URLs/keys/models no seleccionados quedan
  inertes; claves/modelos se resuelven de forma perezosa tras validar el destino.
  Los consumidores execution.py/kimi_client.py conservan sus hashes.
- Las claves y endpoints no aparecen en repr de la configuración/target. Los
  errores propios exponen categorías/códigos, no cuerpo HTTP ni str(exception).
  Se eliminan previews privados de los logs de planner/subagente. No se certifica
  la configuración de logging de callers o bibliotecas externas.
- Las pruebas usan HOME/entorno sintéticos, dotenv bloqueado antes de importar,
  HTTPX MockTransport/registradores y TCP/DNS prohibidos. Warmup y 32 llamadas
  concurrentes observan rutas/headers, no rendimiento o aislamiento físico.
- El snapshot por llamada no es una transacción frente a mutaciones simultáneas
  desde otros threads ni una copia inmutable de messages del caller. No se
  ejecutaron red/proveedores, credenciales reales, hardware o ATTESTED.
- Sin cambios de dependencias/lockfiles, commits, publicación o configuración
  global. Se omite la telemetría global. Los otros clientes del proyecto no se
  consideran corregidos por este cambio de una sola fuente.

## Registro y siguiente lote

Los 598 IDs originales quedan en 549 OPEN, 41 FIXED, 4 MITIGATED y
4 NOT_APPLICABLE. Entre los 582 pendientes iniciales: 544 OPEN, 31 FIXED,
3 MITIGATED y 4 NOT_APPLICABLE. Quedan **543 hallazgos únicos OPEN**:
61 P1, 472 P2 y 10 P3. SW100-R3-0001 permanece FIXED fuera de los 598 IDs.
C0431 y C0135/C0136 siguen OPEN; C0460 sigue MITIGATED.

El [Lote 7 propuesto](PLAN_SWARM100_LOTE7_2026-10-29.md) agrupa C0556/C0557
en fast_smt_gate.py. Su hash permanece intacto y no se ha aplicado.

Se consultaron mediante Context7 las fuentes primarias de
[HTTPX: redirects](https://github.com/encode/httpx/blob/0.28.1/docs/quickstart.md)
y [HTTPX: entorno/proxies](https://github.com/encode/httpx/blob/0.28.1/docs/environment_variables.md).
No había herramientas de grafo expuestas; el descubrimiento fue acotado.
