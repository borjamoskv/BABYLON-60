# Lote 11 ejecutado: persistencia JSON y escritores cooperantes — 29/10/2026

> Alcance de la distribución pública: las referencias marcadas como material no distribuido identifican evidencia o herramientas excluidas deliberadamente de este checkout. Se conservan sus rutas y los resultados históricos; esos soportes no pueden verificarse desde esta distribución.

C0167 (P1), C0168 y C0169 (P2) pasan a FIXED en su alcance reproducido. La
única fuente productiva editada es
`01_KISH_ENGINE/babylon60/core/cortex_persist.py`, distinta de la implementación
BFT cortex_persist_ledger. El
registro reconciliado (material no distribuido: `evidence/swarm100-round3-20261028/registry.json`)
y la validación final (material no distribuido: `evidence/swarm100-lot11-20261029/validation.json`)
conservan estados, comandos, hashes y límites.

**La atomicidad es por archivo. Project, ghosts y system siguen siendo tres
commits separados:** un fallo intermedio puede dejar estado parcial, que ahora
se informa sin anunciar éxito ni deshacer trabajo ajeno.

## Reproducción y aceptación

Las ocho reproducciones previas (material no distribuido: `evidence/swarm100-lot11-20261029/before-tests.log`)
fallaron contra el hash del plan (material no distribuido: `evidence/swarm100-lot11-20261029/before-source-manifest.json`):
escritura parcial que truncaba el JSON anterior, falta de sincronización,
pérdida de actualizaciones en project/ghosts/system, instantes UTC mal etiquetados
en verano/invierno y JSON no finito admitido. HOME fue temporal y se sembró antes
de importar la copia; os.kill del código original estuvo bloqueado.

**944 pruebas pasan y 1 se omite** en la suite acumulada final, incluidas
**55 regresiones del lote**. La omisión corresponde a strike_rs no compilado,
con el módulo bloqueado antes de recoger los tests. Pasan MyPy con
check-untyped-defs, Ruff y los controles documentales. Fuente y tests conservan
sus hashes durante la ejecución final.

La revisión independiente (material no distribuido: `evidence/swarm100-lot11-20261029/independent-review.json`)
aprueba **12 controles en 18 fixtures**, repite las 55 regresiones y Ruff y no
deja hallazgos accionables abiertos. Incluye warmup y ocho consolidaciones con
cuatro hilos, dos proyectos e instancias distintas: tras reabrir conserva las
nueve sesiones y los cambios/decisiones esperados, con el mismo inodo del lock.
Es estrés acotado del protocolo, no una medición de rendimiento o energía.

La revisión añadió dos correcciones: por inspección detectó que sustituir
memory podía desacoplar el lock antiguo de los nuevos destinos; el control
posterior demuestra su rechazo. También reprodujo dinámicamente AttributeError
tras commits parciales con ghosts.alpha=null o sessions_log=[null]. La versión
final conserva completed_files y la causa para ambos. El baseline independiente
y sus logs históricos se preservan. Una suite intermedia de 942 casos quedó
archivada; los 944 anteriores corresponden a la fuente final corregida.

| ID | Corrección | Aceptación observada |
| --- | --- | --- |
| C0167 | Temporal vecino exclusivo, write-all, fsync de archivo, replace y fsync del directorio. | Antes del replace se conserva el JSON anterior; después se reconoce el nuevo contenido visible o estado incierto, con error explícito. No hay truncado del destino en vivo. |
| C0168 | Descriptor flock nuevo por sesión y lock persistente común a base_dir durante todo el RMW. | Hilos/procesos y proyectos distintos conservan sus actualizaciones. Cambiar base/lock mientras opera la sesión provoca rechazo en los casos probados. |
| C0169 | datetime.now(timezone.utc).isoformat() para datos nuevos. | Instantes fijos de verano/invierno conservan su epoch al parsear; timestamps históricos retenidos permanecen intactos. |

## Escritura y resultados de error

El payload es un objeto JSON finito UTF-8 validado antes de abrir un temporal.
Los destinos se limitan al proyecto de la instancia, ghosts y system; deben
existir como archivos regulares, propios y con un único enlace. Se rechazan
rutas desviadas, symlinks y destinos de solo lectura. HOME/.agent/memory y sus
componentes se abren sin seguir enlaces; se valida la identidad de la base
activa y del lock antes de los accesos/reemplazos pertinentes.

El temporal se crea vecino con O_EXCL y modo inicial 0600, se escribe completo
incluidos short writes y se sincroniza. Se conserva el modo básico del destino,
se compara identidad y se reemplaza mediante dir_fd. No se restauran copias
sobre contenido ajeno. Solo se intenta limpiar el temporal creado por esta
operación si su identidad sigue siendo la propia; colisiones/entradas ajenas
permanecen intactas. Fallos de cleanup no ocultan la causa original.

PersistenceWriteError distingue NOT_ATTEMPTED, NOT_REPLACED, REPLACED y UNKNOWN.
Un replace confirmado seguido de fsyncdir fallido puede dejar el JSON nuevo
visible con durabilidad sin confirmar. Si replace lanza, se observa el inodo
para diferenciar reemplazo propio, destino anterior o estado ajeno/desconocido.
ConsolidationError informa completed_files y el archivo/estado actual cuando
está disponible, conservando la causa. No imprime éxito tras fallo ordinario.
Los errores ordinarios dejan de enviar SIGKILL al proceso del operador.

El control AST y de alcance (material no distribuido: `evidence/swarm100-lot11-20261029/scope-check.json`)
confirma SessionDelta, transformaciones de datos y retenciones heredadas intactas.
Los límites de diez cambios recientes y treinta sesiones siguen siendo recortes
intencionales; no son pérdidas por carrera. Los lotes anteriores, dependencias
y lockfiles conservan sus hashes.

## Exclusión y límites

- El lock común es persistente: no se borra, trunca ni sustituye por edad o PID.
  Cada llamada pública usa un descriptor nuevo y lo mantiene desde lectura
  hasta la actualización de los tres archivos. El contexto por hilo revalida
  la base/lock; no comparte un descriptor bloqueado entre todos los hilos.
- Solo coordina escritores que usan el protocolo en el filesystem POSIX local
  probado. _write_json privado ofrece reemplazo por archivo, sin prometer RMW
  protegido a quien lo invoque directamente. No hay aislamiento global frente
  a escritores/lectores ajenos, renombres hostiles, filesystems de red ni todas
  las ventanas entre comprobar identidad y replace.
- No hay journal, recuperación ni transacción conjunta de los tres JSON.
  Se comprueban parciales y fallos antes/después del punto de commit. El archivo
  ya actualizado no se revierte automáticamente si falla el siguiente.
- Las llamadas fsync/replace se ejecutaron realmente en fixtures; no prueban
  un corte eléctrico ni una garantía física del dispositivo. Un hijo desechable
  salió abruptamente durante una escritura temporal: el destino quedó válido,
  pero el temporal huérfano permanece y no se recupera/elimina por conjetura.
- La sustitución cambia el inodo y conserva permisos básicos; no se garantiza
  conservación de ACL/xattrs. La política de archivos propios, sin enlaces y
  topología sin symlinks es más estricta que la lectura/escritura heredada.
- UTC cambia solo timestamps nuevos, sin migrar los históricos ni la presentación
  del operador Europe/Madrid. No es una afirmación de reloj lógico de consenso.
- Toda consolidación/lectura/escritura ocurrió únicamente en HOME temporal propio,
  con TCP/DNS y os.kill original bloqueados antes de importar. Los procesos hijos
  fueron desechables y propios; no se mataron procesos del operador. No hubo
  memoria real, claves/firma/hardware, runtime protegido, publicación o ATTESTED.
  Se omite la telemetría global.

## Registro y siguiente lote

Los 598 IDs originales quedan en **539 OPEN, 51 FIXED, 4 MITIGATED y
4 NOT_APPLICABLE**. Entre los 582 pendientes iniciales: 534 OPEN, 41 FIXED,
3 MITIGATED y 4 NOT_APPLICABLE. Quedan **533 hallazgos únicos OPEN**:
54 P1, 469 P2 y 10 P3. Solo se cierran C0167/C0168/C0169, sin duplicados nuevos.
C0431 y C0135/C0136 siguen OPEN; C0460 sigue MITIGATED.
SW100-R3-0001 permanece FIXED fuera de los 598 IDs.

El [Lote 12 propuesto](PLAN_SWARM100_LOTE12_2026-10-29.md) agrupa C0528/C0529
en ledger_snapshot_engine.py. Solo se prepara; su fuente conserva el hash elegido.

El grafo MCP babylon-60/raíz exacta y la cobertura metadata_match se usaron como
señales best-effort; la búsqueda acotada no identificó consumidores externos
además de la CLI local. Se consultaron mediante Context7 las fuentes primarias
[CPython: replace y descriptores](https://github.com/python/cpython/blob/main/Doc/library/os.rst)
y [CPython: flock](https://github.com/python/cpython/blob/main/Doc/library/fcntl.rst).
Los casos ejecutados delimitan las garantías indicadas.
