# Revisión independiente de la PR #48 — 5 de noviembre de 2026

**Dictamen actualizado: 21 hallazgos aceptados en su alcance local, H09 parcial
y H08 aplazado por decisión del operador.** H10 se cierra tras la
[construcción y prueba de la imagen Docker](H10_DOCKER_VALIDATION_2026-11-05.md).
Las 22 correcciones de código y documentación están presentes; falta la
validación remota de H09 para completar sus criterios. La PR permanece abierta,
sin merge.

La [revisión final con seis revisores nuevos](PR48_FINAL_REVIEW_2026-11-05.md)
confirma los 21 cierres locales tras corregir un consumidor Rust que no compilaba
y declarar el requisito de firma del ejemplo de exportación. Contiene la matriz
y las comprobaciones finales sobre los cambios congelados.

Repositorio: [borjamoskv/BABYLON-60](https://github.com/borjamoskv/BABYLON-60).
[PR #48](https://github.com/borjamoskv/BABYLON-60/pull/48).
Base auditada: `930981ea47a5a4524e9c841338f1fd1a1caceb68`.
Primer commit revisado: `36d45a4575a0295ead265025191427dc2901eb23`.
Este documento acompaña el commit posterior de correcciones independientes;
su dictamen no se atribuye retrospectivamente al primer commit.

## Método y defectos corregidos en esta revisión

Revisores distintos de los implementadores contrastaron los criterios originales
con reproducciones, pruebas y diferencias de código, repartidos en memoria,
autorización/rutas, seguridad, pruebas/documentación, distribución/CI y lógica
formal. Los candidatos corregidos se congelaron y revisores independientes
comprobaron sus hashes. La integración conserva esos bytes, salvo una corrección
de tipos del lector de salida que recibió otra revisión y la repetición de 44
pruebas. Los recuentos de abajo no suman las repeticiones como casos nuevos.

Se reprodujeron y corrigieron:

- **H05, prioridad alta:** un nombre como `-v.b60` producía `-v.lean`, que Lean
  interpretaba como una opción. Su salida cero podía generar un falso VERIFIED.
  Ahora el comprobador recibe bytes capturados por stdin y exige el marcador
  esperado, salida cero y stderr vacío.
- **H05, concurrencia:** dos invocaciones podían reemplazar la misma prueba
  antes de que Lean la leyera. Cada invocación usa bytes y directorio privados;
  publica el archivo atómicamente después de validar. `proof_blake3` identifica
  los bytes comprobados; la ruta publicada sigue siendo un alias reemplazable.
- **H04, defecto residual:** la salida nativa y los errores grandes evitaban
  el límite dentro del worker. El padre limita cada stream a 2 MiB y cada texto
  decodificado a 1 MiB, rechaza esquemas inválidos y termina/recoge el proceso
  tras exceso, timeout o cancelación. El resultado sigue siendo dato no confiable.
- **H20/H21:** la consola describe limpieza lógica de ruta/registro; la guía
  distingue códigos 2 para informe generado sin verificar, 0 con override
  diagnóstico y 1 para un bundle inexistente. Se actualizó también el
  [contrato del prover](../../crates/b60-lang/PROOFS.md).

## Matriz de aceptación

"Aceptado" significa que se satisface el criterio original en el entorno y
alcance indicado. No equivale a certificación de todo el sistema.

| ID | Estado | Evidencia y límite principal |
| --- | --- | --- |
| H01 | Aceptado | Fixtures originales Miri con y sin pin; siete tests nativos/Miri. Estrés independiente: 400.000 publicaciones y 164.326 snapshots coherentes. No prueba todos los órdenes posibles ni clientes ABI externos. |
| H02 | Aceptado | Wheel final instalado sin editable, fuera del checkout, Python 3.11 y cliente MCP real. Initialize, 13 tools, seis resources, lectura, ping y EOF pasan. |
| H03 | Aceptado | 46 tests y sondas CLI/MCP de aprobación, estado y revocación. Una conexión existente observa revocación. Firmas software de prueba; no atestación hardware. |
| H04 | Aceptado | Canario exterior intacto y rechazos OS independientes del AST. Exceso nativo y error grande rechazan; 44 tests pasan tras el cambio final de tipos. Diez cancelaciones repetidas recogen el worker. Alcance: proveedor Darwin y efectos ensayados. |
| H05 | Aceptado | 14 tests CLI, incluidos casos con Lean real: nombres opción, carrera entre comprobadores, mutación y timeout; también se rechazan aliases de fuente. Modelo compilado HALT/NOOP; no corrección del compilador ni ISA completa. |
| H06 | Aceptado con salvedad | Quince auditorías de seguridad sin vulnerabilidades/estados adversos, lock y 47 tests dirigidos; MCP real en Python 3.11. Persiste un aviso previo de metadatos del wheel Z3, explicado abajo. |
| H07 | Aceptado | RustSec exit 0, sin vulnerabilidades ni unsound; 15 tests software P-256/COSE/gate/IPC pasan. Una fixture Swift ignorada. Sin afirmación de firma hardware. |
| H08 | Aplazado | Actions bloqueado por facturación. Se mantiene pendiente por instrucción del operador. Sin pagos ni datos de cuenta modificados. |
| H09 | Parcial | Existen los ocho contextos requeridos y pasan 17 casos locales de selección. La ejecución remota no se acredita mientras Actions esté bloqueado. |
| H10 | Aceptado | Imagen completa Linux ARM64 construida sin caché; CLI, Z3 nativo, recursos empaquetados, MCP stdio/EOF y dashboard HTTP/healthcheck pasan como UID 1000. Sin red exterior ni estado del host; detalle en el informe H10. |
| H11 | Aceptado | Perfil público pasa; omisiones no declaradas y perfil completo incompleto rechazan. Ocho documentos y scopes obligatorios ensayados; fixture del bloque de proyección. |
| H12 | Aceptado | Cuatro tests, 69 rutas CLI y 16 listados respetan rol o selección vacía. Es selección de metadatos, no autorización de efectos. |
| H13 | Aceptado | 75 tests con HTTP loopback real y canario de dispatch; negativos de autenticación, headers, cuerpo y replay no alcanzan provisioner. No se emitieron licencias reales. |
| H14 | Aceptado | 17 tests y seis entrypoints reales: loopback, campos permitidos y errores genéricos. Testigos HTTP/SQLite/socket y canarios sin cambios. |
| H15 | Aceptado | HOME/USERPROFILE temporales, credenciales falsas aisladas, cero red observada y cola canario intacta en los casos ensayados. No certifica toda integración externa. |
| H16 | Aceptado | Cuatro tests pasan y los cuatro rechazan un RuntimeError real sin recibo. Se comprueba discriminación de resultados, no hardware. |
| H17 | Aceptado | Pin en cero, frontera 64/65, wrap, unpin y poison terminal pasan nativo/Miri. |
| H18 | Aceptado | Decoder rechaza opcodes, truncamiento, saltos inválidos, ciclos e ISA no soportada; modelo HALT/NOOP/JUMP y mutación en Lean comprobados. Sin garantía de tiempo para todas las entradas de 4.096 bytes. |
| H19 | Aceptado | Guía y exportador describen evidencia técnica, legal_conformity NOT_DETERMINED y publication_authorized false. No constituye evaluación regulatoria. |
| H20 | Aceptado | Consola y guía limitadas a limpieza lógica; JSON heredado conserva ese alcance explícito. No acredita borrado físico ni ausencia de backups. |
| H21 | Aceptado | Forwarding HTML/JSON/Markdown y códigos 2/0/1 comprobados. La revisión final añade el requisito de clave de software y ejecuta el bloque literal de la guía con y sin configuración; sin autorización regulatoria. |
| H22 | Aceptado | 172 documentos Markdown y 786 enlaces locales sin roturas; 261 referencias históricas marcadas como material no distribuido. URLs externas fuera de esta comprobación. |
| H23 | Aceptado | Proposición y nombre limitados al predecesor compartido; Lean y auditoría de axiomas pasan. No se afirma identidad de entradas ni inyectividad Merkle. |

## Comprobaciones de la integración

- **560 pruebas Python aprobadas**, 87 subtests aparte, tres skips por PowerShell
  ausente y seis deselecciones del alcance original. Las tres baterías originales
  pasan; el total incluye las tres pruebas de distribución del wheel final.
- Tras el último ajuste de tipos se repitieron las **44 pruebas del sandbox**,
  Ruff y MyPy sobre cinco fuentes: todo pasa. Una sonda independiente adicional
  observa diez cancelaciones repetidas, todos los workers recogidos y sin PID vivo.
- `cargo check -q --locked -p b60-lang`: exit 0. Biblioteca: **27 passed,
  dos ignored**; CLI, incluidos casos con Lean real: **14 passed**. El revisor formal repitió
  independientemente los 14 CLI y tres casos del modelo de bytecode.
- Wheel final SHA-256:
  `21ff1938e36816f550e56fee026349f7d17625ccfaa1a3d83545b597b5c4636b`.
  Sus 394 archivos de fuente coinciden con el código empaquetado e instalado.
  Python 3.11.16, SDK MCP 2.3.0, sin PYTHONPATH y fuera del checkout: CLI,
  initialize, tools/resources, lectura, ping y cierre EOF con salida cero.
- Ruff sobre Python modificado, actionlint, lock, semántica documental,
  presupuesto y topología pasan. Antes del commit se comprueban también enlaces
  de documentos modificados y topología del índice. Presupuesto y semántica usan
  alcance workspace; configuración global y listeners quedan excluidos explícitamente.

Los logs, sondas y matriz JSON detallada se conservan en el expediente local de
revisión; no se distribuyen como parte de este documento. Los tests reproducibles
sí forman parte de la PR. Los fallos ambientales por falta de espacio y el primer
fallo de MyPy se conservan; sus reintentos satisfactorios están separados.

```sh
uv sync --locked --extra dev --extra gemini
uv run --locked pytest tests/test_chaos_parent_resource_limits.py tests/test_chaos_execution_boundary.py tests/test_audit_cli_output_scope.py tests/test_cli_compliance_forwarding.py -q
BABYLON60_TEST_WHEEL=/ruta/al/wheel-final.whl uv run --locked pytest tests/test_mcp_distribution_contract.py -q
cargo check -q --locked -p b60-lang
cargo test --locked -p b60-lang --lib
cargo test --locked -p b60-lang --test prove_cli -- --include-ignored --test-threads=1
python3 scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only
python3 scripts/c5_quality_gates/audit_token_budget.py --workspace-only --skip-ghost-listeners
python3 scripts/guards/verify_active_topology.py
python3 scripts/guards/verify_active_topology.py --staged
```

## Límites y pendientes

H06 satisface su criterio original de seguridad, pruebas y MCP. `uv pip check`
sigue terminando en 1 por etiquetas de plataforma contradictorias del wheel
upstream de `z3-solver`: el registro del lock es idéntico al de la base y la
importación real funciona. Se conserva como seguimiento de distribución; no se
declara una instalación sin avisos ni ejecución de todos los extras.

H09 restaura el contexto que faltaba, pero presencia de checks no equivale a
ejecución aprobada. También se observaron condiciones previas en las que claims
se omite en PR y SAST se omite tras un requisito fallido; las protecciones no se
modificaron. H10 tiene construcción y smoke completos en Linux ARM64; se añadió
dockerignore y se comprobó la exclusión de estado local. El listener sigue en
loopback del contenedor y no se presenta como accesible con un publish bridge.

Los límites del prover se describen en [PROOFS.md](../../crates/b60-lang/PROOFS.md):
subconjunto puro, host confiable y limpieza de descendientes comprobada en Unix.
Ni las pruebas software ni los hashes acreditan atestación hardware, conformidad
legal, efectos productivos o una nueva certificación de release.

Los trailers del commit conservan el ámbito `source-snapshot`: BLAKE3 de rutas
ordenadas, NUL, longitud de ocho bytes big-endian y contenido, usando el destino
literal para symlinks. Las secuencias declaradas acompañan las iteraciones de
fuentes de esta PR; no es un
ledger BFT ni un recibo de runtime. Se conserva la firma SSH y los hooks Git.

No se han realizado pagos, cambios de protección, release, merge ni auto-merge.
