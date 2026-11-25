# Correcciones de snapshots, digests y pruebas Z3 — 30/10/2026

Base de trabajo: `5a3be92a62963585fe9530e5a3b7dca5ff109742`. Trabajo local
en una rama aislada, sin push.
La integración posterior incorpora `main` en
`fdef72d277426a61246c5fb8bb1404d4efe7d2a3`, incluidos procedencia 6D,
Flash Defense y las regresiones SWARM100 del lote 12, conservando sus archivos
y sus pruebas. El paquete raíz declara BLAKE3 1.8.5 como dependencia de
desarrollo del PoC; esa versión ya estaba en el lockfile y no se actualizan
paquetes ni dependencias productivas. El primer candidato fue `2aef1202a019daa36b3985f8e957e846c2400671`;
se incorporaron los avances posteriores antes del cierre. El último commit
documental de `main` añade el informe de auditoría y su evidencia. El corte
anterior incorporó las correcciones y regresiones del PoC de Navier–Stokes.
La extensión solicitada `fdef72d2` añade regresiones del parser, préstamos,
rechazo del oráculo ausente y emisión Lean comprobada, incluidos sus dos
casos que requieren Lean instalado y el oráculo nativo.

## Memoria compartida

`SharedManifestRing0` almacenaba dos `PayloadSlot` ordinarios en `UnsafeCell`.
Una segunda publicación podía sobrescribir el slot que un consumidor estaba
copiando. Comparar `control_word` después de la copia no hace lícita esa carrera.
El caso reproducible usa la fuente real, un productor y un consumidor con pin.

El almacenamiento interno pasa a palabras atómicas. Una barrera Release anterior
a la escritura, junto con la barrera Acquire posterior a las cargas del lector,
permite rechazar una generación que haya sido sobrescrita. Solo se entrega el
snapshot al llamador cuando ambas lecturas de control coinciden.

Un CAS de admisión rechaza productores concurrentes sin esperar; su bandera usa
un byte del relleno de `WriterControlLine`. La publicación final usa CAS para no
reabrir un canal envenenado durante la escritura. Agotar la generación provoca
estado terminal en lugar de permitir un ABA por desbordamiento.

Se conservan 512 bytes totales, alineación de 128 y offsets de control, pin y
slots: 0, 128 y 256. `PayloadSlot` conserva sus 128 bytes de copia, incluido su
relleno. El tipo Rust del almacenamiento interno cambia a `AtomicPayloadSlot`;
los consumidores deben usar `read_snapshot`, sin copiar los slots compartidos
mediante accesos ordinarios. No se certifican consumidores externos al repositorio.
La lectura tiene reintentos acotados y puede fallar por contención; no se declara
una lectura sin reintentos ni una garantía de latencia.

Reproducción Miri sin modificar lockfiles del repositorio:

```sh
python3 tests/miri_shared_manifest_ring0/run.py --seeds 0 1 7 23 42
cargo test --locked -p babylon60_root --lib ring0_
cargo run --release --locked -p babylon60_root --example poc_stress_manifest_ring0_512b
```

El runner Miri requiere el componente nightly ya instalado y su sysroot.
Crea un paquete temporal sin dependencias e importa la fuente del checkout.
Las semillas cubren ejecuciones concretas; no son una prueba exhaustiva de todas
las intercalaciones posibles. El estrés informa rechazos y corrupciones observadas.

## Validación de evidencia

Los tres registros de `finding_contract` rechazan valores distintos de 64
caracteres hexadecimales y mantienen el rechazo del digest SHA-256 vacío.
Las mayúsculas hexadecimales admitidas anteriormente se conservan.

Procedencia exige el prefijo exacto `b3:` seguido de 64 dígitos hexadecimales
ASCII para exportación, ancla externa y recibo de ejecución. La integración
conserva la compatibilidad de `main` con letras mayúsculas en esos metadatos;
las identidades calculadas siguen siendo canónicas en minúsculas y la
comparación de identidad de contenido sigue siendo exacta.
Los digests esperados mal formados se rechazan sin error de tipos. Un sobre con
evidencia mal formada no asciende de `CLAIMED` ni obtiene `ATTESTED`.
Esto valida estructura y correspondencia declarada; no autentica por sí solo
una exportación remota ni sustituye la autorización de efectos.

```sh
uv run --locked pytest tests/test_finding_evidence_contract.py tests/test_provenance_digest_validation.py tests/test_fl027_provenance_authority.py -q
```

Los contraejemplos y hashes históricos permanecen en
[la auditoría de base](AUDIT_PENDING_COMMITS_2026-10-30.md). Las regresiones nuevas
son el control de aceptación actual; no se reescribe la evidencia histórica.

## Procesos del solver

La suite `semantic_solver_adapter` comparte un presupuesto de procesos externo
entre sus casos. El guard se adquiere antes de comenzar el plazo medido del caso,
incluido el control negativo de 30 ms. El comando usa el paralelismo habitual del
harness; no requiere `--test-threads=1`. La exclusión entre casos no controla
la carga externa: una repetición registró `Timeout` en un caso positivo bajo
el plazo productivo de 2 s. Los casos funcionales usan ahora un plazo de pared
de 10 s, acotado y exclusivo de pruebas, para no confundir corrección del
parser/protocolo con tiempo de arranque y planificación del host. La prueba
negativa de 30 ms mantiene su plazo y comprueba terminación y limpieza. Esto
no acredita que el solver cumpla 2 s en un host compartido. No se modifican los límites productivos,
la autenticación del binario, la reserva durable ni los tests de replay concurrente.

```sh
cargo test --locked -p babylon60-compiler --test semantic_solver_adapter
cargo test --locked -p babylon60-compiler --test solver_trust
```

Estos tests requieren Z3 y un pin de prueba aprobado mediante `BABYLON_Z3_BIN` y
`BABYLON_Z3_BLAKE3`. El pin histórico no debe confundirse con cualquier ejecutable
llamado `z3` en PATH. La validación registra ruta, versión y BLAKE3 del fixture;
no cambia confianza productiva ni configuración global.

No se realiza otro intento Touch ID. La evidencia hardware anterior conserva su
candidato original; tampoco se declara CI remota aprobada para esta rama local.
