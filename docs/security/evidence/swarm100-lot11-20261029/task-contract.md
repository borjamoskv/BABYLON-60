# Contrato — Lote 11 (29/10/2026, Europe/Madrid)

C0167/C0168/C0169: única fuente productiva editable core/cortex_persist.py.
Reproducir primero en HOME/.agent/memory temporal sembrado antes de importar
copia del módulo. Bloquear os.kill del original y TCP/DNS; jamás memoria real
ni procesos del operador. Sin dependencias/lockfiles, commits/push, hardware,
ATTESTED ni runtime protegido. Preservar cambios ajenos/evidencia histórica.

Ring-0 (persistencia/rutas), Ring-1 (carreras), Ring-2/3 (evidencia/salida).
Escritura temporal vecina exclusiva, payload validado, write-all/fsync,
replace por archivo y fsync de directorio. Antes de replace: destino anterior
intacto. Después: JSON nuevo visible, fallo/durabilidad incierta explícitos.
No rollback ciego. Exclusión POSIX común a base_dir de escritores cooperantes
sobre todo crystallize_session, no solo por proyecto. No borrar locks por edad.
UTC ISO aware conserva instantes nuevos; no reescribir históricos.

Project/ghosts/system siguen tres commits por archivo, no una transacción.
Declarar progreso/parciales al fallar; ningún éxito de consolidación si falla
una etapa. Privado _write_json solo garantiza reemplazo por archivo; lectores/
escritores que ignoran el protocolo y cortes eléctricos no certificados.
Rechazar rutas/projectid/symlinks pertinentes; errores por excepción explícita
sin SIGKILL del operador. Mantener esquema/retenciones heredadas.

Aceptación: red/green por ID, fault-injection y bytes/inodos/reapertura,
barreras threads/procesos/proyectos, reloj fijo verano/invierno, suite,
Ruff/MyPy, revisión independiente, registro y controles documentales.
Preparar Lote12 sin aplicar. Grafo babylon-60/raíz exacta, metadata_match
best-effort; caller observado CLI local, sin ejecución de esa CLI real.
