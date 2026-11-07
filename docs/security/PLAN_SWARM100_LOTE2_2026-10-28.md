# Lote 2 propuesto: conservación de datos y alcance de purgas — 28/10/2026

Estado: ejecutado bajo autorización, con cuatro P1 corregidos y C0460
MITIGATED. [Resultado y verificación](REMEDIATION_SWARM100_LOTE2_2026-10-28.md).
Los hashes iniciales constan en la
[selección](evidence/swarm100-lot1-20261028/lot2-selection.json).
Después del Lote 1 no quedan P1 OPEN con dictamen REPRODUCED; este bloque
selecciona cinco P1 CONFIRMED_STATIC y una copia duplicada. Primero deben
reproducirse en fixtures; este plan no acredita su ejecución ni su corrección.

| Orden | IDs | Archivos | Objetivo |
| --- | --- | --- | --- |
| 1 | C0460 | `scripts/c5_cortex/autoconsolidate.py` | Conservar originales hasta persistir y verificar un reemplazo íntegro. |
| 2 | C0018 | `01_KISH_ENGINE/babylon60/commands/itera.py` | Impedir que la purga automática borre WAL/SHM por sufijo. |
| 3 | C0219 | `scripts/repatriated/c5_sharur_100_anergy_purge.py` | Confinar la limpieza y preservar todos los diarios SQLite. |
| 4 | C0387 y su duplicado C0562; C0563 | `tools/skill_library/global/anergy-purge-protocol/scripts/anergy_purge.py` y copia en `c5-cortex-swarm-orchestrator/references/modules/` | Preservar WAL/SHM y evitar acceso implícito a sesiones globales desde una purga de workspace. |

## Reproducción y criterios de aceptación

**C0460.** Usar una tabla temporal con IDs de texto, payloads distintos y
orden causal, forma que alcanza el DELETE actual. Conservar evidencia de
conteo y contenido antes/después. Identificar el esquema real y los consumidores
antes del parche. El reemplazo debe conservar los datos necesarios y guardarse
en la misma transacción que el borrado; una excepción, ID inválido o fallo de
persistencia debe conservar íntegros los originales. Añadir casos de repetición
e intercalación de escritores. Si falta un contrato que permita implementar
la consolidación, rechazarla sin borrar datos y registrar MITIGATED, sin fingir
una funcionalidad completa.

**C0018 y C0219.** Crear SQLite WAL con autocheckpoint desactivado y filas
confirmadas que aún dependen del WAL. Ejecutar solo el helper aislado en el
directorio temporal y demostrar el fallo previo. La corrección no debe tratar
WAL/SHM como cachés ni borrarlos por extensión. Probar datos consultables por
un lector nuevo, escritor activo, bases ajenas y fallo de inspección. No ejecutar
el revisor completo, cohortes globales, Git ni recorridos reales de proyectos.

**C0387/C0562.** Reutilizar el mismo arnés en ambas copias. `--dry-run` debe
conservar los datos y el modo ordinario también debe preservar los diarios.
Cualquier mantenimiento SQLite requiere propiedad y coordinación demostradas;
en su ausencia la operación se rechaza o informa sin borrar. Un checkpoint
aislado no demuestra que no existan escritores concurrentes.

**C0563.** La purga de un workspace no debe abrir ni actualizar por omisión
`conversation_summaries.db` del usuario, tampoco para contar supuestos ghosts.
Probar con un HOME temporal y dos sesiones de workspaces distintos, manteniendo
ambas activas. Espiar el acceso a la ruta global para verificar su ausencia;
no consultar datos reales. Una futura limpieza de sesiones necesita una
operación separada con autorización, ámbito y comprobación de vida específicos.

## Ejecución propuesta

1. Fijar fuentes/hashes y reproducir cada escenario con SQLite temporal real.
2. Aplicar cambios solo a los cinco archivos del bloque. Preservar copias,
   cuerpos originales y rollback; ninguna purga debe ampliar su ámbito.
3. Añadir regresiones e intercalaciones con calentamiento, conservando fallos
   y límites; no convertir estos ensayos en una afirmación de rendimiento.
4. Ejecutar pytest dirigido y batería existente relacionada con `--locked`,
   Ruff, MyPy, revisión independiente y controles documentales.
5. Actualizar estados y duplicados solo tras comprobar el efecto. Mantener
   OPEN/MITIGATED donde falte funcionalidad o garantía de conservación.

La ejecución se limitó a sus cinco fuentes. El
[Lote 3](PLAN_SWARM100_LOTE3_2026-10-28.md) queda solo planificado. Sin claves,
datos, sesiones o configuración del operador, dependencias nuevas, commit ni despliegue.
