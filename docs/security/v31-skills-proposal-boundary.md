# V1 / v3.1 — Frontera entre propuesta y ejecución de skills

Fecha: 1 de noviembre de 2026. Alcance: catálogo, gateways Rust/Python y
regresiones locales. El diagnóstico recibido describía como pendientes componentes
ya presentes en el checkout. Se conservaron las tres metaoperaciones, el broker,
el dispatcher y el prompt normalizado; se corrigieron los fallos reproducidos.

## Fallos observados y cambio

| Caso | Antes | Ahora |
| --- | --- | --- |
| Registro sellado | Cuatro skills diferían del snapshot actual; fallaba la prueba del catálogo Rust. | Las dos copias de `skills-lock.json` coinciden con el snapshot: 131 entradas y 26 skills físicas de workspace. |
| Pin de arranque | Rust podía derivar el registro al iniciar; Python no contrastaba un pin. | Ambos servidores cargan el registro junto al catálogo y rechazan ausencia o divergencia. La distribución Python incluye el pin. |
| Integridad del contrato | Rust contrastaba identidad y digest, pero aceptaba cambios en campos de política. | Se compara el contrato completo, incluidos `effect_profile` y `guard_invariants`. |
| Identidad de la propuesta | Versión por defecto y digest opcional. | Versión y digest explícitos y coincidentes con la skill inspeccionada. |
| Estado de la propuesta | `VERIFIED` sin ejecución y campos de cliente como supuesta observación independiente. | `AUTHORIZED`, `effects_executed=0`, alcance `proposal_only` y ninguna postcondición marcada como comprobada. |
| Evidencia del cliente | `simulated_execution_result` podía conducir a `Verified` en el broker. | Se rechaza con `UNTRUSTED_EXECUTION_EVIDENCE` antes de emitir capacidad o consumir nonce. |

La emisión intencional de un nuevo pin sigue disponible mediante
`--emit-lockfile`. Revisar su diff y sincronizar las copias raíz y `docs/` antes
de aceptarlo. Un pin protege contra divergencias respecto al contenido revisado;
no autentica a quien pueda sustituir simultáneamente el catálogo y el pin.

## Evidencia reproducible

Las [regresiones Rust](../../crates/babylon-skills-mcp/tests/proposal_boundary.rs)
reprodujeron cuatro fallos antes de la corrección. Las
[regresiones Python](../../tests/test_skills_proposal_boundary.py) reprodujeron
el falso `VERIFIED`. Ambas suites rechazan evidencia fabricada, incluidos hashes
coincidentes entre sí y valores vacíos, con 10 calentamientos y 100 repeticiones
por caso. El fichero testigo permanece intacto.

El test Rust de ejecución usa un archivo temporal: un ejecutor que declara un
hash sin escribir falla ante la lectura independiente; una escritura real con
hash concordante llega a `Verified`. Una segunda ejecución con la misma capacidad
se rechaza. El [test del dispatcher](../../tests/test_fl_mcp01_dispatch.py)
confirma con un lector SQLite separado que una propuesta aceptada no autoriza
por sí sola una escritura. Sus firmas de prueba no son atestación hardware.

Comprobaciones ejecutadas:

```sh
cargo test --locked -p babylon-skills-mcp
cargo build -q --locked -p babylon60_root --lib --features python
BABYLON60_TEST_CAPABILITY_LIBRARY="$PWD/target/debug/libbabylon60.dylib" \
  uv run --locked pytest tests/test_skills_proposal_boundary.py \
  tests/test_cortex_mcp_server.py tests/test_fl_mcp01_dispatch.py \
  tests/test_skills_installed_distribution.py -q
uv run --locked mypy --follow-imports=silent \
  01_KISH_ENGINE/babylon60/mcp/skills_snapshot.py \
  01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py
```

Resultado funcional: 24 pruebas Rust y 70 Python pasan, sin omisiones en la
ejecución con el módulo nativo. Incluye el arnés existente de 100.000 llamadas
Rust, la comprobación por stdio y la carga del paquete Python instalado fuera
del checkout. Estas pruebas no miden rendimiento ni consumo energético.
Ruff, mypy sobre los dos módulos modificados, auditor semántico, presupuesto,
topología y `git diff --check` también pasan. `Cargo.lock` y `uv.lock` no cambian.

## Límites del contrato

`skills.propose_effect` evalúa una propuesta. Las credenciales, épocas, trazas
y precondiciones recibidas no se convierten por ello en autenticación remota ni
en observación del sistema de archivos. El host sigue siendo responsable de
proveer contexto fiable y de vincularlo al efecto que autoriza. FL-P09 se prueba
dentro de la traza declarada; no demuestra contención entre trazas arbitrarias.

La ejecución Rust usa callbacks del host de confianza. Los efectos Cortex
conservan el [dispatcher y gate firmados](fl-mcp01-authority-drift.md); el JSON
`action_capability` no los sustituye. No se certifica aislamiento del sistema
operativo, biometría Secure Enclave, persistencia de nonces de propuesta tras
reinicio ni garantías formales Z3/Lean. Esas propiedades quedan `NO_VERIFICADO`
en esta comprobación local. No se consultó CI remoto.

El cierre documental se limita al workspace: auditor semántico, presupuesto con
`--skip-ghost-listeners` y topología. No incluye configuración global ni telemetría
de listeners del anfitrión.
