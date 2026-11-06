# Lote 2: diarios SQLite y conservación de datos — 28/10/2026

## Contrato previo a las ediciones

Ejecutar el [plan](PLAN_SWARM100_LOTE2_2026-10-28.md) solo en sus cinco fuentes:
ITERA, cohorte 1 repatriada, autoconsolidación y ambas copias anergy_purge.
Reproducir antes de editar con SQLite temporal real y preservar los hashes.
Comprobar conservación de datos, destinatarios ajenos, enlaces, fallos de
inspección y ausencia de acceso implícito a sesiones globales. Aplican los
[contratos de persistencia y descriptores](../03_guides/agent_contracts.md).

La búsqueda acotada en `01_KISH_ENGINE`, `scripts/c5_cortex`, `tests` y
`docs/01_spec` solo localiza el stub JournalEntry del propio script, sin esquema
ni consumidor que defina una consolidación válida. C0460 se rechazará antes de
abrir la base y quedará MITIGATED; no se inventará un formato persistente ni se
declarará una funcionalidad completa. La mitigación debe conservar originales
y no impedir escrituras ajenas.

Las limpiezas no clasificarán WAL/SHM/journals por sufijo como huérfanos ni
los eliminarán. Se eliminarán archivos elegibles individualmente con
descriptores relativos y O_NOFOLLOW, preservando SQLite por nombre/encabezado,
directorios protegidos y objetos no inspeccionables. No se borrarán directorios
recursivamente; los vacíos podrán permanecer. La cohorte 1 se limita al cwd o
workspace explícito. Las cohortes 2–5 y el main masivo quedan fuera del cierre.

Fixtures: archivos/SQLite bajo directorios temporales, HOME temporal y
credenciales inexistentes. ITERA heredado se reproduce con un ejecutor de find
limitado al directorio de la fixture; no se lanzan find/rm ni el revisor Git.
No datos o sesiones del operador, redes, dependencias nuevas, commit ni despliegue.

## Resultado

**C0018, C0219, C0387 y C0563 quedan FIXED. C0460 queda MITIGATED**, con
consolidación no disponible y rechazo antes de conectar. C0562 hereda FIXED
de C0387; C0388 se reconoce como otra copia del reset global de C0563 y hereda
su corrección. Se modificaron únicamente las cinco fuentes previstas.

| Ámbito | Comportamiento comprobado |
| --- | --- |
| ITERA | Se eliminan solo archivos `.pyc` con el magic de esta versión de Python, bajo cwd y mediante descriptores relativos; no hay find/rm de journals ni borrado recursivo de directorios. |
| Cohorte 1 | Se limita a cwd o workspace explícito. Conserva SQLite y directorios; solo limpia bytecode identificado. No usa las raíces globales WORKSPACE/CORTEX para esta cohorte. |
| Ambas purgas | Seleccionan archivos individuales, protegen nombres SQLite/journals/superjournals y encabezados conocidos, usan O_NOFOLLOW y revalidan inode. Las rutas protegidas, enlaces y objetos no inspeccionables se conservan. |
| Sesiones globales | No se resuelve HOME ni se abre la base global, en dry-run o modo ordinario; contadores cero y estado NOT_CHECKED. |
| Consolidación | La API y load/merge/save rechazan con CONSOLIDATION_UNSUPPORTED. No hay resolución de ruta, apertura, creación ni DELETE. La CLI devuelve 2. |

## Verificación ejecutada

- [Hashes iniciales](evidence/swarm100-lot2-20261028/before-source-manifest.json):
  cinco fuentes coincidentes con el plan antes de editar.
- [PoC de consolidación](evidence/swarm100-lot2-20261028/consolidation-before.json):
  el helper original eliminó **tres filas SQLite reales y no guardó reemplazo**,
  únicamente en una base temporal con payloads sintéticos.
- [Regresiones previas](evidence/swarm100-lot2-20261028/before-tests-confined.log):
  **44 failed, 2 passed**, con HOME lógico y cwd temporales antes de importar.
  La primera ejecución equivalente y su código de test también se conservan.
- [Batería final relacionada](evidence/swarm100-lot2-20261028/related-tests.log):
  **322 passed, 1 skipped**, catorce archivos. Incluye 80 regresiones del lote.
  La omisión existente requiere `strike_rs`, no construido en este entorno;
  no se afirma haber ejecutado toda la suite del repositorio.
- Las regresiones cubren WAL confirmado sin checkpoint, lector nuevo y escritor
  activo, SQLite bajo scratch/out/cache o nombres `.tmp/.pyc`, encabezados
  disfrazados, superjournals, enlaces, errores de inspección, dos sesiones
  activas, dry-run y rechazo de la consolidación antes de crear una base.
  En ambas copias hay tres rondas de calentamiento más veinte intercalaciones
  programadas con un escritor SQLite real en otro hilo; sobreviven las 24 filas
  y `integrity_check` devuelve `ok`. No se mide rendimiento.
- [Revisión independiente](evidence/swarm100-lot2-20261028/independent-review.json):
  80 regresiones y siete ensayos adversariales aprobados; sin bloqueantes en
  el alcance. Incluye fallo de unlink, FIFO, cambio de inode antes de la
  revalidación y rechazo antes de convertir db_path.
- Ruff y MyPy pasan en las cinco fuentes. Se retiraron dos variables/imports
  sin uso y se renombró una variable de recibo para corregir deuda de tipos
  preexistente; no cambió la lógica de las demás cohortes.
- [Validación final](evidence/swarm100-lot2-20261028/validation.json): comandos,
  salidas, hashes, enlaces, controles documentales y contabilidad.

La reproducción ITERA tradujo exclusivamente los comandos find heredados a
operaciones de la fixture. No se ejecutaron find/rm, strict_reviewer, main de
cohortes ni ningún recorrido global. El resto de helpers se ejercitó como
Python real sobre archivos/SQLite temporales.

## Límites del cierre

C0460 permanece MITIGATED: no se ha implementado una consolidación que conserve
payloads y persista reemplazos de forma transaccional. El bloqueo preserva los
originales y no impide que otro escritor opere. Recuperar la funcionalidad exige
un contrato de esquema, representación y consumidores, no una operación DELETE
ni una certificación documental.

Las protecciones cubren nombres reservados y encabezados SQLite conocidos; no
identifican formatos cifrados arbitrarios disfrazados como artefactos. Los
descriptores y la comprobación de identidad reducen carreras, pero no hacen
atómico el check de tipo seguido de unlink ante un actor hostil que renombre
después del último stat. No se acredita aislamiento del sistema operativo.

Las cifras de bytes son tamaños lógicos de archivos desvinculados, no espacio
físico liberado en APFS/NAND ni energía. Dry-run contabiliza candidatos, con
cero eliminaciones/bytes retirados. Los directorios vacíos permanecen.

La corrección de cohorte 1 no certifica las cohortes 2–5 ni su main. C0223
continúa OPEN: la limpieza `.lake` de cohorte 2 no se ejecutó ni corrigió; se
refrescaron su hash y referencias sin cerrar el hallazgo.

## Registro y siguiente lote

Quedan **556 hallazgos únicos OPEN** del inventario original: 72 P1, 474 P2 y
10 P3. Hay cuatro registros MITIGATED y el P1 adicional SW100-R3-0001 sigue
OPEN fuera de los 598 IDs originales. La reducción desde 562 combina cuatro
correcciones P1, una mitigación P1 y una deduplicación P2. En los 582 IDs de la
ronda: 557 OPEN + 18 FIXED + 3 MITIGATED + 4 NOT_APPLICABLE = 582.

Los [cambios por ID](evidence/swarm100-lot2-20261028/candidate-status-updates.json)
conservan historia y hash vigente. El validador distingue rangos históricos
de archivos posteriormente acortados y exige límites actuales a los nuevos
dictámenes; su [control dirigido](evidence/swarm100-lot2-20261028/validator-check.json)
confirma que un rango actual inválido sigue rechazándose.

El [Lote 3](PLAN_SWARM100_LOTE3_2026-10-28.md) está preparado sobre autorización
y publicación: C0413, C0418 y SW100-R3-0001, en dos scripts sin editar.
No se ejecutaron Git remoto, biometría, campañas o sesiones del operador,
ni se modificaron dependencias, lockfiles, commits o despliegues. Los controles
documentales son locales; se omiten configuración global y telemetría de ghost listeners.
