# Revisión final independiente de la PR #48

**Confirmados 21 arreglos en su alcance local.** H06 conserva la salvedad de
metadatos Z3 descrita abajo. H08 sigue aplazado y la validación remota de H09
permanece pendiente. No se realiza merge ni auto-merge.

Seis revisores nuevos, distintos de los implementadores anteriores, examinaron
los criterios originales y el diff de la [PR #48](https://github.com/borjamoskv/BABYLON-60/pull/48)
desde `930981ea47a5a4524e9c841338f1fd1a1caceb68` hasta
`7928a23863aa8bc9d2593714dacf0f477834a3f4`. Dos implementadores separados
prepararon las correcciones siguientes; sus revisores originales las volvieron
a comprobar. La batería integrada final se ejecutó sobre esos cambios congelados.
Las evidencias de fallo del head inicial se conservan separadas de los reintentos.

## Problemas encontrados y corregidos

1. **Regresión de compilación del ejemplo Ring-0.** La encapsulación de memoria
   había hecho privados dos campos que el ejemplo seguía usando. Cargo fallaba
   con dos errores E0616. Ahora emplea `ffi_pin` y la consulta pública del estado
   terminal, sin reabrir acceso a los campos. Compilación y ejecución oficiales
   pasan, también en la repetición independiente. El ejemplo cuenta lecturas
   rechazadas y comprueba muestras/publicaciones reales; sus textos ya no
   presentan layout o tiempos observados como certificación física o wait-free.
2. **Prerequisito de firma omitido en H21.** El ejemplo de exportación alcanzaba
   el parser, pero sin una clave configurada fallaba antes de generar el informe.
   La guía declara ahora una semilla Ed25519 de software de 32 bytes/64 caracteres
   hexadecimales, ya exportada mediante el mecanismo de secretos de la instalación.
   El propio bloque comprueba su presencia antes de invocar la CLI. No activa
   firmas efímeras ni convierte esa firma en autorización regulatoria o hardware.
   La prueba ejecuta el bloque extraído de la guía con CLI, ledger, firmador y
   exportador reales, con identidad y clave explícitas de prueba.

No se modificaron las bibliotecas de ejecución, las dependencias ni los lockfiles.
Las correcciones afectan al ejemplo Rust, la guía y su prueba de integración.

## Matriz de cierre local

| ID | Dictamen | Comprobación final principal |
| --- | --- | --- |
| H01 | Aceptado | Fixtures originales con/sin pin, Miri Stacked/Tree; siete regresiones nativas/Miri y estrés de 400.000 publicaciones. Ejemplo consumidor corregido y ejecutado. |
| H02 | Aceptado | Wheel no editable en Python 3.11, stdio externo y SDK real: 13 tools, seis resources, lecturas y EOF; copia alterada del corpus rechazada. |
| H03 | Aceptado | 28 comprobaciones de setup/gate y lector MCP persistente: autorización ligada al contenido y revocación visible inmediatamente. |
| H04 | Aceptado | Proveedor Darwin real, canario externo intacto, denegaciones OS, salida nativa acotada y cancelación con procesos recogidos; sin aumento de descriptores observado. |
| H05 | Aceptado | 14 tests CLI y matriz externa del checker: bytes/marca/digests, nombres opción, concurrencia, publicación y timeout con descendientes ausentes. |
| H06 | Aceptado con salvedad | 24 auditorías de base/extras/plataformas/versiones sin avisos de seguridad, lock y MCP probados; salvedad Z3 conservada. |
| H07 | Aceptado | RustSec sin vulnerabilidades/unsound; 15 tests software de P-256, gate e IPC pasan. Una fixture Swift ignorada y dos avisos de mantenimiento declarados. |
| H08 | Aplazado | Pendiente por instrucción del operador; sin cambios de pagos o cuenta. |
| H09 | Local verificado; remoto pendiente | 31 tests dirigidos, 17 escenarios de selección nativa, actionlint y revisión de nombres requeridos. No se certifica ejecución hosted. |
| H10 | Aceptado Linux ARM64 | Build previo sin caché inspeccionado y runtime nuevo del mismo ID, con 30 pasos correctos; CLI, Z3, MCP/EOF, HTTP y healthcheck, UID 1000 y aislamiento. |
| H11 | Aceptado | Perfiles público/completo, omisiones negativas y fixture real del mirror pasan. |
| H12 | Aceptado | 64 casos de rol/ámbito/consulta sin selecciones incompatibles; caso sin coincidencia rechaza. |
| H13 | Aceptado | HTTP loopback real: autenticación, contenido, origen y replay comprobados antes del canario de dispatch. No licencias reales. |
| H14 | Aceptado | Entrypoints reales del dashboard legado conservan loopback, campos permitidos y errores genéricos. |
| H15 | Aceptado | Casos aislados de HOME/credenciales, cero red observada y canario intacto; alcance de las pruebas identificado. |
| H16 | Aceptado | Tests y seis mutaciones de resultados incorrectos distinguen error de éxito; no se acepta un recibo vacío como atestación. |
| H17 | Aceptado | Cero, límites 64/65, wrap, unpin y estado terminal en nativo/Miri; ejemplo usa la API pública. |
| H18 | Aceptado | 55.986 secuencias bytecode ensayadas; las 218 aceptadas coinciden con la VM. Decoder y Lean rechazan codificación inválida. Solo el subconjunto modelado. |
| H19 | Aceptado | Exportes reales en cinco idiomas y tres formatos conservan alcance técnico, conformidad pendiente y publicación no autorizada. |
| H20 | Aceptado | Guía, consola y JSON delimitan limpieza lógica de ruta/registro, sin promesa de borrado físico. |
| H21 | Aceptado | Ejemplo literal genera HTML con clave configurada; sin clave o con valor vacío rechaza antes de CLI, sin traceback ni archivo. Siete tests de forwarding/guía pasan. |
| H22 | Aceptado | 174 documentos y 792 enlaces locales sin roturas en el head inicial; 261 referencias históricas conservan ruta y marca de material no distribuido. Nuevos enlaces también comprobados. |
| H23 | Aceptado | Lean fijado y contraejemplo independiente confirman solo predecesor compartido; no identidad de entradas ni inyectividad Merkle. |

H09 queda fuera de los 21 cierres completos: su corrección local se verifica,
pero su criterio remoto sigue pendiente junto con H08.

## Verificación integrada y reproducción

- **570 pruebas Python aprobadas**, 87 subtests aparte, tres skips por PowerShell
  ausente y seis deselecciones del alcance original. Antes de las dos nuevas
  pruebas del ejemplo documentado se habían repetido 568 casos sobre el head inicial.
- Ruff sobre Python modificado y MyPy sobre seis fuentes pasan; actionlint,
  `uv lock --check`, diff, semántica, presupuesto, topología y enlaces pasan.
  La topología del índice se comprueba antes del commit.
- Memoria: fixtures originales Miri con y sin pin en Stacked y Tree Borrows;
  siete tests pasan en nativo y en ambos modelos. Estrés independiente:
  400.000 publicaciones, 169.384 lecturas coherentes y cero venenos observados.
- Ejemplo Rust corregido: Cargo compila y ejecuta con `--locked`; la repetición
  independiente observa 500.000 publicaciones, 37.825 snapshots aceptados,
  6.573 lecturas rechazadas, cero retrocesos y cero hashes incorrectos.
- Formal: 18 tests Rust dirigidos, 21 casos externos y elaboración Lean del
  teorema Merkle pasan. La enumeración diferencial es finita, no una prueba de
  toda la ISA ni de corrección del compilador.
- Docker: se vuelve a probar la imagen
  `sha256:7c514bcb3085ff9d3fc89e4ba9f69a39cf8388448077fabda420b5b3e9949a10`.
  Dockerfile, lock, aplicación y recursos contrastados; los cambios posteriores
  de esta revisión son guía, prueba y ejemplo Rust. No se repite ni se atribuye
  un nuevo build a la ejecución `runtime_only`. El perfil queda detenido y el
  contexto original permanece intacto. Véase el [informe H10](H10_DOCKER_VALIDATION_2026-11-05.md).

```sh
uv run --locked pytest tests/test_cli_compliance_forwarding.py tests/test_audit_cli_output_scope.py tests/test_smoke_docker.py -q
cargo test --locked -p babylon60_root --example poc_stress_manifest_ring0_512b --no-default-features --features microkernel --no-run -j 2
cargo run --locked -p babylon60_root --example poc_stress_manifest_ring0_512b --no-default-features --features microkernel -j 2
cargo test --locked -p b60-lang --test prove_cli -- --include-ignored
python3 scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only
python3 scripts/c5_quality_gates/audit_token_budget.py --workspace-only --skip-ghost-listeners
python3 scripts/guards/verify_active_topology.py
```

Los fixtures, comandos, hashes y logs detallados se conservan en el expediente
local de esta revisión; no se distribuyen con este documento. Las pruebas y el
ejemplo corregidos sí forman parte de la PR. Las comprobaciones documentales
excluyen configuración global y omiten explícitamente telemetría de listeners.

## Límites retenidos

El fallo previo de `uv pip check` por etiquetas de plataforma contradictorias
del wheel upstream Z3 en macOS se conserva: su registro no cambió y la prueba
SAT funciona. H06 satisface el criterio original de seguridad/pruebas/MCP; no se
declara una instalación sin avisos ni ejecución de todos los extras.

Pruebas finitas y de software no certifican todos los entrelazados, hardware,
latencia, RFO, false sharing, borrado físico, conformidad legal o producción.
El pin Ring-0 vigila un lector lógico; no reserva memoria para varios lectores.
El prover verifica el subconjunto descrito en su contrato, no toda la ISA.
Docker se limita a Linux ARM64 y HTTP en loopback del contenedor. No se renueva
el manifiesto histórico del release. La firma Git y los trailers de snapshot
identifican fuentes, sin constituir un ledger BFT ni un recibo de runtime.

H08 y la validación remota de H09 permanecen pendientes. La PR queda abierta,
sin merge ni auto-merge y sin cambios a las protecciones de la rama principal.
