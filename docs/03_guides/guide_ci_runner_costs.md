# Distribución de runners de CI

Las pruebas generales de Python (3.11 y 3.12), Rust y calidad usan Linux.
`python-tests.yml` conserva la suite completa y la compilación de `babylon-attest`;
`ci.yml` conserva check, tests y Clippy con dependencias bloqueadas y Protobuf.

macOS se reserva para dos ámbitos:

- `macos-native.yml` ejecuta BYPASS-001, que comprueba el confinamiento real con
  Seatbelt y se omite en Linux. Se activa para cambios de código Rust, dependencias,
  configuración de compilación o su propia prueba/workflow, y bajo demanda.
  Los cambios ordinarios de Python o documentación no lo disparan.
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
