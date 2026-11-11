# Distribución de runners de CI

Las pruebas generales de Python (3.11 y 3.12), Rust y calidad usan Linux.
`python-tests.yml` conserva la suite completa y la compilación de `babylon-attest`;
`ci.yml` conserva check, tests y Clippy con dependencias bloqueadas y Protobuf.
`python-tests.yml` exige Landlock (`BABYLON60_REQUIRE_LANDLOCK=1`) para los tests de
confinamiento: si el runner no lo ofrece, fallan en vez de omitirse.

macOS se reserva para tres ámbitos:

- `macos-native.yml` ejecuta BYPASS-001, que comprueba el confinamiento real con
  Seatbelt y se omite en Linux. Se activa para cambios de código Rust, dependencias,
  configuración de compilación o su propia prueba/workflow, y bajo demanda.
  Los cambios ordinarios de Python o documentación no lo disparan.
- `confine.yml` ejecuta los tests de `babylon60 run`, `demo` y `log` contra el kernel
  real: Landlock en `ubuntu-latest` y `sandbox-exec` (Seatbelt) en `macos-15`. Solo lo
  disparan cambios en `01_KISH_ENGINE/babylon60/confine/`, en `tests/test_confine_*.py`
  o en el propio workflow, además de la ejecución manual.
- El job `claims` de `ci.yml` conserva la certificación completa y sus artefactos
  en macOS. Se activa al publicar un tag `v*` o mediante `workflow_dispatch` con
  `full_release_evidence=true`. El valor predeterminado es `false`.

Una CI ordinaria en verde no certifica todos los claims de release ni sustituye
la atestación biométrica interactiva. La certificación completa sigue siendo
necesaria antes de declarar esas garantías para una versión. Cada ejecución
manual o por tag puede consumir minutos facturables según la cuota de la cuenta.

Los jobs de macOS tienen plazo máximo y cancelación de ejecuciones reemplazadas.
Esta distribución reduce uso de runners caros; no fija un presupuesto ni garantiza
un coste mensual. Los planes, pagos y límites de facturación se gestionan aparte.
