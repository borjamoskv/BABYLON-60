# Lote 7 propuesto: veredictos y recibos del gate — 29/10/2026

Estado: ejecutado por instrucción del operador; véase el
[informe de cierre](REMEDIATION_SWARM100_LOTE7_2026-10-29.md).
La planificación histórica agrupaba dos P1 CONFIRMED_STATIC/OPEN
en una fuente productiva prevista: `scripts/c5_verifiers/fast_smt_gate.py`.
La [selección con hash](evidence/swarm100-lot6-20261029/lot7-selection.json)
fija la versión a reconfirmar antes de editar. No quedan P1 OPEN con
reproducción previa; se elige este grupo por afinidad y por sus afirmaciones
no comprobadas de verificación/compliance.

| ID | Fallo a reproducir | Resultado exigido |
| --- | --- | --- |
| C0556 | Constantes True y existencia de rutas se convierten en SYSTEM_SOUND_AND_COMPLIANT sin ejecutar las comprobaciones declaradas | Cada resultado requiere una comprobación real y su alcance; ausente/no ejecutado debe seguir UNKNOWN/NOT_EXECUTED y no producir éxito del gate. |
| C0557 | Digest sólo de IDs y prefijo sig_ed25519_ simulan un recibo firmado/compliance | Ligar ID, resultado, detalle y configuración relevantes; no inventar firma ni certificación legal. Sin firmante real, recibo explícitamente UNSIGNED. |

Primero reproducir en copia temporal, con HOME/root propios, los modos JSON y
recibo, invariantes fallidos y no ejecutados. Cambiar resultados/detalles
manteniendo IDs y comprobar que cambia su digest. Observar salida y exit code,
no dar por probado un sistema por su etiqueta. Nunca ejecutar el mantenimiento
soberano ni escribir recibos/ledgers del operador.

Diseño pendiente: separar observación de verdict, distinguir UNKNOWN/UNTESTED de
PASS y hacer que el exit code represente las comprobaciones exigidas. Si no hay
checker de una invariante, declararlo sin cerrar su prueba mediante constantes.
La existencia de una ruta sólo permite afirmar esa existencia. Mantener un
contrato serializado explícito para el exportador; conservar recibos históricos
sin regenerarlos o reinterpretarlos como firmas del contrato nuevo.

Revisar el consumidor daily_sovereign_maintenance por inspección y dobles de
subproceso, sin modificarlo automáticamente ni convertir un recibo en permiso
de despliegue. Usar claves de software sólo para pruebas matemáticas aisladas
si fueran necesarias; nunca crear ATTESTED ni simular firma hardware/SCITT real.

Aceptación: red/green por ID; casos de fallo, UNKNOWN y datos cambiados; salida
JSON/código de retorno coherentes; suite relacionada, Ruff/MyPy, revisión
independiente, registro reconciliado y controles documentales. Sin publicación,
hardware, solver/proceso nativo protegido, red o claves reales. La ejecución
posterior se documenta en el informe enlazado. C0431, C0135/C0136 y C0460
conservan sus estados pendientes.
