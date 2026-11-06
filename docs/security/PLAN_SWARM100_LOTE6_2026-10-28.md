# Lote 6 ejecutado: selección y transporte de proveedores — 28/10/2026

Estado: ejecutado el 29/10/2026 bajo autorización posterior; véase el
[informe de corrección](REMEDIATION_SWARM100_LOTE6_2026-10-29.md). Agrupó dos P1 inicialmente
CONFIRMED_STATIC/OPEN por afinidad en una fuente productiva prevista:
`01_KISH_ENGINE/babylon60/kernel/swarm_orchestrator.py`. No quedan P1 OPEN
con reproducción previa. La [selección con hash](evidence/swarm100-lot5-20261028/lot6-selection.json)
fijó la versión antes de editar; la ejecución respetó la fuente única.

| ID | Fallo a reproducir | Resultado exigido |
| --- | --- | --- |
| C0132 | Backend desconocido deriva silenciosamente al proveedor remoto | Rechazar el selector inválido antes de construir cliente, resolver credenciales o enviar el prompt. Valores locales/remotos válidos conservan su ruta explícita. |
| C0133 | URL HTTP de un host remoto permitido transporta prompt y credencial | Exigir HTTPS en proveedores remotos antes de preparar petición/Authorization; preservar únicamente el HTTP local que autorice su contrato. |

Reproducciones aisladas: dobles de cliente/transporte que registren llamadas sin
red, prompts de fixture y credenciales sintéticas. No leer variables de claves
reales ni construir clientes con fallbacks del entorno del operador. Comparar
cero intentos de transporte ante selector inválido, HTTP remoto, URL malformada,
userinfo o host ajeno; positivos de local/remoto deben comprobar destino exacto,
headers y payload sin conexión real.

Diseño pendiente: selección exhaustiva sin fallback remoto, validación de URL
por proveedor y rechazo antes de efectos. Revisar redirecciones y handlers sin
ampliar automáticamente la fuente prevista ni introducir una segunda ruta que
salte la validación. Mantener timeouts, cancelación, límites de reintento y
secretos fuera de mensajes/diagnósticos.

Aceptación: red/green por ID, regresiones de las rutas válidas y rechazo temprano,
suite relacionada, revisión independiente, Ruff/MyPy y reconciliación del registro.
Consultar documentación vigente de la biblioteca HTTP antes del parche. Sin
proveedores, red, credenciales, servicios nativos o hardware reales.

La ejecución posterior se limitó al módulo y a fixtures sin red/credenciales
reales; no ejecutó proveedores ni hardware. C0431 del ledger y C0135/C0136
del verificador histórico v2 permanecen OPEN; necesitan alcance propio. C0460
sigue MITIGATED. No quedan resueltos por estas correcciones de enrutamiento.
