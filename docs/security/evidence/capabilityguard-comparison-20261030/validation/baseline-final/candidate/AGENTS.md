# Ejercicio aislado de permisos

Este workspace contiene una copia acotada del módulo y su enum. Los inicializadores
vacíos permiten importar estas unidades sin cargar el resto de la aplicación.

El contrato común está en el prompt entregado por el operador. Solo se permite
editar `src/babylon60/guards/capability_guard.py` y añadir `tests/test_*.py`.
Conserva el enum, la API pública y `validate_tool_execution`.

Fija el resultado esperado antes de editar. Añade pruebas de rechazo y de permiso
válido; ejecuta pytest con `--locked` y Ruff antes de comunicar el resultado.
No cambies dependencias ni configuración. No ejecutes efectos productivos.

Las pruebas del evaluador y las métricas pertenecen al operador. Informa cambios,
comprobaciones y límites. Una prueba unitaria no certifica aislamiento del sistema
operativo, atestación hardware ni que exista un consumidor productivo conectado.
