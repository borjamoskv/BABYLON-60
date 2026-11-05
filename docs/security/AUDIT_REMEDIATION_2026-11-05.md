# Correcciones de la auditoría pública del 5 de noviembre de 2026

Base auditada: `930981ea47a5a4524e9c841338f1fd1a1caceb68` del repositorio
`borjamoskv/BABYLON-60`. Esta revisión corrige localmente 22 de los 23 hallazgos.
H08, el bloqueo de facturación de GitHub Actions, queda pendiente por decisión
del operador. Este documento registra resultados locales y sus límites; no
certifica un despliegue ni renueva la evidencia del release histórico.

La [revisión independiente posterior de la PR #48](PR48_INDEPENDENT_REVIEW_2026-11-05.md)
detectó y corrigió defectos residuales en H05, el límite de salida de H04 y la
presentación de H20/H21. El [cierre posterior de H10](H10_DOCKER_VALIDATION_2026-11-05.md)
añade construcción y prueba Docker completas: **21 hallazgos con aceptación
local completa**, H09 con aceptación parcial y H08 aplazado.
La [revisión final independiente](PR48_FINAL_REVIEW_2026-11-05.md) vuelve a
comprobar esos cierres y registra las dos últimas correcciones verificadas.
La [salvedad de distribución Z3 se ha resuelto](Z3_INSTALLATION_VALIDATION_2026-11-05.md)
con una versión oficial corregida e instalaciones limpias sin avisos.
Los resultados siguientes conservan la evidencia del primer commit;
la revisión enlazada recoge las comprobaciones del candidato corregido.

## Estado por hallazgo

| ID | Prioridad | Corrección y aceptación local |
| --- | --- | --- |
| H01 | P1 | Slots atómicos, propiedad temporal del escritor por CAS y preservación de poison. Los fixtures originales pasan Miri con y sin pin; siete regresiones y 40.000 publicaciones concurrentes no detectaron inconsistencias. |
| H02 | P1 | Ambos locks de skills corresponden al corpus; el guard permanece activo. La rueda instalada fuera del checkout responde a initialize, tools/list, ping y EOF. |
| H03 | P1 | CLI, MCP y setup comparten resolución del gate; estado legacy exige selección explícita. Firma software y revocación se comprueban sobre la misma base. |
| H04 | P1 | Confinamiento OS obligatorio en el backend Darwin validado, sin fallback inseguro ni hash presentado como firma SCITT. Cálculo y NumPy funcionan; lectura/escritura exterior, red y fork son rechazados con testigos independientes. |
| H05 | P1 | prove compila la fuente real, llama al Lean fijado y registra BLAKE3. La fuente inválida rechaza; HALT/NOOP verifica. |
| H06 | P2 | Dependencias Python corregidas y mínimo 3.11. pip-audit base/extras: cero avisos; gate CI analiza doce destinos de plataforma/versión. |
| H07 | P2 | Familias P-256 y Tokio actualizadas y API adaptada. cargo audit --deny unsound pasa con cero vulnerabilidades y cero unsound. |
| H08 | P2 | Pendiente: facturación de GitHub Actions; no se cambian pagos ni datos de cuenta. |
| H09 | P2 | El workflow restaura el contexto requerido rust (macos-latest). La clasificación dentro del workflow evita checks pendientes por filtros de rutas; ante clasificación desconocida se ejecuta el test nativo. |
| H10 | P2 | Cerrado posteriormente: imagen Linux ARM64 completa construida sin caché y probada; CLI, Z3, MCP y dashboard/healthcheck pasan. Véase el informe H10 enlazado. |
| H11 | P2 | Perfil público declarado mediante marker y generado por mirror. El perfil completo sigue rechazando fuentes ausentes y el público informa su omisión explícita. |
| H12 | P2 | El enrutamiento filtra rol antes de seleccionar y no devuelve candidatos de otro rol. |
| H13 | P2 | Pedidos HTTP autenticados y ligados al contenido; validación de Host, Origin, cabeceras y replay antes del provisioner. No se emitieron licencias reales durante las pruebas. |
| H14 | P2 | El dashboard legado delega en la implementación mantenida: loopback, campos previstos y errores genéricos. |
| H15 | P2 | Pruebas con HOME/USERPROFILE temporales, timeout y transporte Kimi ficticio, sin credenciales ni cola reales. |
| H16 | P2 | La prueba de atestación exige rechazo y recibo vacío sin backend; resultados de error ya no pasan por falta de aserciones. |
| H17 | P2 | Presencia del pin separada del tick: cero, frontera 64/65, wrap y estado terminal comprobados. |
| H18 | P2 | API fallible con decodificación HALT/NOOP/JUMP, bytes exactos, destinos y terminación. 0xFF, truncamiento, saltos inválidos y ciclos rechazan; Lean rechaza codificación mutada. |
| H19 | P2 | La guía describe evidencia técnica y evaluación regulatoria pendiente. |
| H20 | P2 | La guía distingue eliminación lógica de borrado físico y certificación persistente. |
| H21 | P2 | Forwarding y ayuda de compliance corregidos; ejemplo con formato e inputs explícitos. |
| H22 | P3 | 261 referencias históricas conservadas como texto marcado no distribuido; 102 documentos comprobados sin enlaces locales rotos. |
| H23 | P3 | Nombre y comentario del teorema limitados al predecesor compartido; no se afirma identidad ni inyectividad Merkle. |

## Validación ejecutada sobre la integración

- Python 3.12: **537 pruebas aprobadas**, 87 subtests aparte, tres skips por
  PowerShell ausente y seis deselecciones del alcance de la auditoría. Los 17
  casos MCP que fallaban originalmente pasan.
- Wheel no editable, Python 3.11.16, fuera del checkout: cuatro comandos CLI y
  MCP por stdio con 13 herramientas y cierre EOF satisfactorios.
- `cargo check -q --workspace --locked`; seis tests SPSC y siete Ring0 pasan.
  Los fixtures originales pasan Miri; siete casos pasan con Stacked Borrows y
  siete con Tree Borrows. El estrés dirigido usa calentamiento y 40.000
  publicaciones; no acredita todos los órdenes de ejecución posibles.
- b60-lang: 27 tests de biblioteca y siete de CLI con Lean real pasan; dos
  casos previos permanecen ignorados. Se elaboraron 19 módulos Lean; sus fuentes
  finales coinciden y el módulo de H23 se volvió a elaborar.
- pip-audit: cero avisos en 29 paquetes base y 173 con extras. RustSec pasa;
  siguen avisos de mantenimiento de derivative y unsafe-libyaml.
- Ruff sobre Python modificado, MyPy dirigido, actionlint, resolución de lock,
  enlaces, semántica documental, presupuesto y topología pasan. El presupuesto
  omite configuración global y telemetría de listeners expresamente.

Para reproducir, usar Python 3.11 o posterior y las toolchains fijadas:

```bash
uv sync --locked --extra dev --extra gemini
uv run --locked pytest tests/test_state_paths_and_cli_gate.py tests/test_chaos_execution_boundary.py tests/test_onboarding_http_authorization.py tests/test_native_ci_scope.py -q
uv run --locked pytest tests/test_cortex_mcp_server.py -k 'not rust_babylon_skills_mcp_stdio_interop and not detonate_ephemeral_bomb and not cmd_mcp_bomb_cli and not cli_tools_and_skills_introspection' -q
cargo check -q --workspace --locked
cargo test --locked -p b60-lang --test prove_cli -- --include-ignored
cargo audit --deny unsound --json
python3 scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only
python3 scripts/c5_quality_gates/audit_token_budget.py --workspace-only --skip-ghost-listeners
python3 scripts/guards/verify_active_topology.py
```

La prueba de distribución acepta `BABYLON60_TEST_WHEEL` apuntando a la rueda
final y comprueba origen, initialize y tools/list desde otro directorio.
Los tests de firma software no acreditan Secure Enclave ni Touch ID.

Los trailers `Ledger-Head` y `Ledger-Seq` del commit describen una declaración
de snapshot de fuentes, con ámbito `source-snapshot` y secuencia inicial cero.
El head es BLAKE3 de las rutas ordenadas y sus bytes (symlinks por su destino
literal); se separan ruta y contenido con NUL y longitud de ocho bytes big-endian.
Estos metadatos y su control de sintaxis no acreditan un ledger BFT ni atestación
hardware. La firma SSH del commit conserva su propio ámbito de autenticidad Git.

## Compatibilidad y pendientes

- Python mínimo **3.11**, necesario para las dependencias corregidas.
- SharedManifestRing0 conserva layout de 512 bytes y alineación de 128, pero
  exige accesos atómicos de todos los participantes. No es compatible con
  clientes antiguos que copien slots directamente; no se promete wait-free.
- La ejecución dinámica solo se habilita con el backend Darwin/Python
  framework validado. Las demás configuraciones devuelven rechazo explícito.
- El prover de fuente verifica HALT/NOOP; la API de bytecode admite además
  JUMP. Los efectos y el resto de la ISA quedan fuera del modelo y se rechazan.
- H09 requiere que el workflow llegue a la rama correspondiente y se ejecute
  remotamente; la protección de rama no se debilita ni se modifica aquí.
- Docker completo se verificó posteriormente en Linux ARM64, según el informe
  H10. La ejecución remota de H09 y H08 siguen pendientes.
- El manifiesto histórico de release no se regenera: su verificador rechaza el
  nuevo árbol por diferencias de hashes. Esta rama no es una nueva certificación
  de release ni autoriza su publicación.
- El test de flood de stdout de otro módulo MCP se interrumpe también en el
  baseline; se conserva como fallo previo fuera de estos 23 hallazgos.

No se ejecutaron efectos productivos, pagos ni atestación biométrica. La PR debe
permanecer abierta para revisión; este trabajo no incluye merge.
