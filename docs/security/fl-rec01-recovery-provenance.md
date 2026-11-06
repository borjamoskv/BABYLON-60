# Recuperación con evidencia durable

26 de octubre de 2026. Se corrigen los dos caminos de confirmación sin evidencia
identificados en la [auditoría inicial](experimental-audit-plan-2026-10-26.md).
La recuperación conserva la incertidumbre cuando falta una intención durable
o una observación suficiente del efecto. Los resultados cubren estas rutas
locales de SecureFS; la campaña completa de FL-REC-01 sigue pendiente.

## Comportamiento corregido

En [`recover_quarantined`](../../src/secure_fs.rs):

- Sin intención WAL se devuelve `InvalidStateTransition`, tanto si falta la
  cuarentena como si contiene un objeto. No se destruye ese objeto ni se
  fabrica un recibo.
- La intención o recibo debe corresponder a `Delete`, dispositivo, inodo y hash
  previo esperados, con el hash posterior nulo propio del borrado. Un recibo
  de otro efecto u objeto se rechaza antes de usarlo.
- Una intención pendiente con cuarentena ausente devuelve
  `AmbiguousOutcomeRequiresReconciliation`; conserva su estado WAL. No se
  convierte en éxito ni en prueba de que el efecto no ocurrió.
- La cuarentena se abre respecto al descriptor, sin `Path.exists()`. Los
  symlinks y errores de acceso no se interpretan como ausencia.
- Una cuarentena válida con intención coincidente se verifica y destruye;
  se sincroniza el directorio antes de persistir `OutcomeKnown`. Si falla
  cualquiera de esos pasos, no se devuelve `Committed`.
- Un recibo conocido y coincidente permite devolver el resultado histórico
  sin repetir el efecto, también después de reconstruir el orquestador.

En `reconcile_wal_entry`, `Delete + ENOENT` devuelve
`OutcomeRemainsAmbiguous` sin modificar el WAL. Un renombrado o borrado externo
no acredita la ejecución de la operación reservada. Se conserva la
reconciliación legítima de mutaciones mediante identidad e hashes.

Los casos positivos existentes de NEMESIS establecen ahora explícitamente la
intención durable antes de pedir recuperación. No se amplían permisos, se
introducen estados nuevos ni se modifican dependencias o lockfiles.

## Regresiones y evidencia

[`fl_rec01_recovery_provenance.rs`](../../tests/fl_rec01_recovery_provenance.rs)
contiene once pruebas: ausencia de intención con y sin objeto en cuarentena;
intención reservada o incierta; renombrado y borrado externos; recibos
incompatibles; symlinks reales y colgantes; preimagen intacta; recuperación
legítima persistida; fallo de escritura del recibo; fallo de sincronización del
directorio; y estrés acotado de los dos caminos originales.

Los testigos comprueban bytes, dispositivo e inodo mediante accesos al
filesystem separados de la respuesta del orquestador. Son fixtures temporales
con observación local; no constituyen un observador fuera de un host hostil.
Los reinicios de estas regresiones reconstruyen el orquestador y recargan el
WAL; no simulan un corte físico de alimentación.

| Comprobación | Antes | Después |
| --- | --- | --- |
| Primera suite de nueve regresiones | 3 pasan y 6 fallan. | Las 11 regresiones finales pasan. |
| Recuperación sin intención, 128 pares medidos tras 10 calentamientos | 128 confirmaciones indebidas. | 0 confirmaciones indebidas. |
| Reconciliación por ausencia tras renombrado, mismos pares | 128 recibos indebidos. | 0 recibos indebidos. |
| Fallo de sincronización del directorio tras un borrado observado | El WAL recargado contiene `OutcomeKnown`. | El WAL recargado conserva `AttemptReserved`. |

El fallo de sincronización se inyecta únicamente en un backend de pruebas:
tras el borrado nativo, `dup2` sustituye atómicamente el descriptor propio de
cuarentena por un pipe. Su `fsync` falla; se comprueba el registro persistido
tras reconstruir un orquestador nativo. No se modifica el backend productivo ni
se cierra un descriptor con una ventana de reutilización entre hilos.

Verificación final:

```sh
cargo test -q --locked -p babylon60_root --test fl_rec01_recovery_provenance --test adversarial_nemesis --test nemesis_wave3 --test nemesis_wave4 --test nonce_instance_regressions -- --nocapture
cargo test -q --locked -p babylon60_root --lib secure_fs:: -- --nocapture
rustfmt --check tests/fl_rec01_recovery_provenance.rs
```

Resultado: 77 tests pasan, sin omisiones: 11 regresiones nuevas, 28 casos
NEMESIS adversariales, 15 de Wave III, 10 de Wave IV, 6 de nonces y 7 unitarios
de SecureFS. Incluyen controles positivos de recuperación idempotente,
reconciliación de mutaciones y rechazo de replay. El formato de la prueba nueva
y el control de espacios de las rutas modificadas pasan.

Pasan también el auditor semántico, el presupuesto local, la topología y los
enlaces locales de ambos informes. Se excluyen la configuración global y la
telemetría de ghost listeners. Los 40 archivos con modificaciones ajenas
registrados al inicio conservan sus bytes. El control global de espacios sigue
fallando en `tests/test_markov_bridge.py:145`, por una línea vacía final ajena
a esta corrección; el control de las rutas de esta tarea pasa.

## Alcance pendiente

El formato WAL existente no distingue los recibos históricos legítimos de los
que pudo promover incorrectamente el código anterior. Los recibos conocidos se
aceptan bajo la premisa de ledger confiable; esta corrección asegura las
transiciones nuevas ensayadas y no certifica retroactivamente todo
`OutcomeKnown`. Resolver ese problema requiere procedencia adicional o una
migración explícita.

No se ha ejecutado la campaña comparativa completa A/B/C de 5.000 casos,
compactación de contexto ni aislamiento de procedencia entre sesiones. La
[sonda original](evidence/recovery-audit-2026-10-26.rs) conserva las aserciones
del contraejemplo histórico: con el código corregido deja de reproducirlo y
falla intencionadamente. Las regresiones de aceptación vigentes son las once
pruebas enlazadas arriba.
