# CORTEX PTC: presencia a través del framing JSON-RPC

Fecha: 2026-11-18. HEAD inspeccionado: `ab35f40f0d81f70cb95071c02e6bd0e98e7a4af8`.
Prueba inicial del generador y del framing productivos con herramienta sintética
y cliente de referencia. Esta ejecución no verificó una ruta OpenAI/DSH real.
La integración OpenAI se implementó y verificó después en el
[informe del adaptador](cortex-openai-adapter-20261118.md); este documento conserva
los resultados y límites de la etapa inicial.

## Contrato

Resultado: conservar ausencia, null y cadena vacía al comparar argumentos
recibidos y estado final; iniciar cada ruta y caso con `nota="original"`.
Rutas de esta prueba: [vectores](../../tests/fixtures/cortex_ptc_presence.json),
[tests](../../tests/test_cortex_ptc_presence.py) y este informe.
Sin cambios propios de producción, dependencias, lockfiles o autorización;
sin llamadas facturables, persistencia de notas ni despliegue.

El checkout tiene escritores concurrentes. Otro chat, «Probar ausencia frente a
null», también trabaja sobre esta cuestión y reemplazó el primer informe de
esta sesión. Se conserva su trabajo. Este archivo documenta exclusivamente la
ejecución de `test_cortex_ptc_presence.py`, que reutiliza el framing de CORTEX.
Los cambios concurrentes en módulos MCP no se atribuyen ni integran aquí.

## Resultado observado y límites

| Intención | Argumentos capturados | Estado observado | Directa / referencia |
| --- | --- | --- | --- |
| Conservar | `{}` | `{"nota": "original"}` | Coinciden |
| Borrar | `{"nota": null}` | `{"nota": null}` | Coinciden |
| Vaciar | `{"nota": ""}` | `{"nota": ""}` | Coinciden |

El [generador](../../01_KISH_ENGINE/babylon60/mcp/cortex_ptc_ralph.py) emite un
`Protocol`, no un cliente ejecutable. La prueba compila sus declaraciones y el
cliente **exclusivo del test** usa `Signature.bind` sin aplicar defaults. Conserva
las claves suministradas antes de serializar. La ruta directa usa el diccionario
del vector. Ambas pasan por `_read_message`, `handle_frame`, `process_request`
y `_write_message` de `CortexMCPServer`, con streams en memoria y un handler
sintético que actualiza la nota. No se prueba un proceso MCP externo, el despacho
de herramientas productivas, sus permisos ni un validador de JSON Schema.

Los vectores adaptan `description/schema/tests/data` de
[JSON Schema Test Suite](https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/validation/README.md),
añadiendo oráculos locales de argumentos y estado. No se ejecuta ni certifica la
suite upstream.

Se comprobó además que el generador produce `nota: str | None = None` tanto para
una propiedad opcional `string` como para otra `string|null`. Se pierde una
distinción descriptiva entre opcionalidad y nulabilidad. No demuestra un cambio
de argumentos: el colapso ocurre si un consumidor materializa el default, cosa
que no hace el `Protocol` por sí solo. No se localizó ese consumidor en los
emisores, tests, scripts de memoria y configuración inspeccionados.

OpenAI puede ser un consumidor futuro, pero requiere conectar la ejecución.
Según su [guía oficial](https://developers.openai.com/api/docs/guides/function-calling),
`strict: true` exige todas las propiedades en `required`; null no sustituye la
omisión de este contrato. Una integración debe conservar opcionalidad con
`strict: false` explícito y validación propia, o representar la operación
conservar/borrar/asignar y comprobar su traducción a MCP. Ninguna opción se ha
instalado o ejecutado contra la API en esta prueba.

## Evidencia y reproducción

| id | description | status | evidence |
| --- | --- | --- | --- |
| PRESENCE | Tres intenciones, dos rutas y dos oráculos | passed | 3 casos de `test_direct_and_reference_projection_preserve_intent` |
| ORACLE | Detectar pérdida pese a respuestas ok iguales | passed | 3 casos de `test_oracles_detect_loss_despite_identical_ok_responses` |
| LIVE | Consumidor PTC real hasta MCP | pending | NO_VERIFICADO: cliente de referencia, sin OpenAI/DSH |

```sh
uv run --locked pytest tests/test_cortex_ptc_presence.py tests/test_cortex_ptc_ralph.py -q
uv run --locked ruff check tests/test_cortex_ptc_presence.py
uv run --locked mypy --follow-imports=silent tests/test_cortex_ptc_presence.py
python3 scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only
python3 scripts/c5_quality_gates/audit_token_budget.py --workspace-only --skip-ghost-listeners
python3 scripts/guards/verify_active_topology.py
```

La ejecución dirigida aprobó **38 tests**, incluidos 6 nuevos. Ruff y mypy
aprobaron el archivo nuevo; mypy sigue imports silenciosamente y no certifica
sus tipos. Contratos, presupuesto y topología aprobaron. Se omiten reglas
globales y telemetría de ghost listeners.

Control de sensibilidad adicional: al sustituir el método del cliente de
referencia solo dentro del proceso pytest por otro que ejecuta
`kwargs.setdefault("nota", None)`, el caso conservar falló por recibir
`[{"nota": None}]` en vez de `[{}]`. Fallo inducido esperado; ningún archivo fue
modificado por ese control. Los otros controles eliminan null o valores falsy
y detectan los cambios de estado correspondientes.

Decisión: conservar la prueba local y no introducir un sentinel en producción
sin demostrar que un consumidor real colapsa las intenciones. Tampoco se afirma
equivalencia operativa completa ni ahorro de tokens medido.
