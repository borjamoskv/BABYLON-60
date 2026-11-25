# Corrección de los 11 hallazgos de skills de proyecto

Fecha: 2026-10-30. Origen: auditoría de `.agents/skills` en la revisión pública `00f20e7890d40f072bd0904bf55affb20e972eb5`. Alcance del cierre: fuentes canónicas locales, distribución de workspace y ejemplos publicados en esas skills. No se ha publicado el cambio ni desplegado el runtime.

**Resultado: 11/11 hallazgos atendidos y comprobados en su alcance.** F08 y F10 ya estaban corregidos en el checkout local; se conservaron sin cambios. F09 estaba parcialmente corregido. Se preservaron también dos reglas de `thermo-audit` presentes en la distribución local pero ausentes de su fuente canónica, incorporándolas a esta antes de la regeneración final.

| ID | Cambio o corrección conservada | Comprobación y límite |
| --- | --- | --- |
| F01 · P1 | Simplificar modifica la respuesta y conserva los artefactos. El módulo audit-only no ejecuta borrados. | Escenario independiente: archivo inicial conserva hash y mtime. No demuestra obediencia universal de un LLM. |
| F02 · P1 | Halt terminal a POISONED; commit por CAS; campos privados y rechazo antes del wrap del contador. | Contraejemplo del halt antes del CAS, parada repetida, rechazo posterior y carrera real de escritor/halt. Agotar reintentos devuelve Contended explícito sin escrituras del lector; el supervisor decide el halt. |
| F03 · P1 | Retirada la receta con payload UnsafeCell no atómico. La referencia usa accesos atómicos SeqCst y copia local validada. | Lectores concurrentes, payload coherente y Miri con proveniencia estricta. Sin certificación de IPC productivo. |
| F04 · P2 | Inicialización válida de AtomicU64 y miembros C++17 estándar; capacidad no nula y tipo copiable. | Cargo aislado con --locked, compilación C++17 estricta y FIFO/saturación/vaciado en 100 ciclos. |
| F05 · P2 | Lector Python de exportaciones estables: copia bytes de un mmap de lectura, sin vistas exportadas. | Tamaño exacto, estados inválidos, lecturas repetidas y liberación del archivo. Se retiró la pretensión de lectura IPC en vivo; no se probó un mapping nombrado Windows. |
| F06 · P2 | Linter explícitamente léxico; JSON v2 incluye cobertura, archivos, exclusiones y conformidad no verificada. | Blanco sobre blanco y botón vacío no reciben certificación global. La evaluación del contraste y accesibilidad renderizados sigue fuera de este script. Directorios sin fuentes devuelven 2. |
| F07 · P2 | Launcher relativo al checkout, REA_CLI externo explícito y plist generado desde rutas verificadas con WorkingDirectory. | Distribución reubicada, espacios y caracteres XML, rutas ausentes/relativas rechazadas, plutil; ningún servicio instalado. |
| F08 · P2 | Conservada la separación local entre atestación hardware P-256 y firmas Ed25519/SCITT. | Revisión del procedimiento final y hash idéntico al inicial; no se generaron claves ni atestaciones. |
| F09 · P2 | Conservada la corrección de apple-bypass; eliminada la exigencia de hf_transfer en thermo-audit. | Revisión de ambos módulos y referencia a la migración oficial. Sin descargar modelos ni ejecutar purge. |
| F10 · P2 | Conservado adaptive-cron: observables atribuidos, incertidumbre y decisión de sesión del operador. | Escenario independiente con 40 minutos y dos fallos: sin diagnóstico, corte ni automatización. |
| F11 · P2 | /grill-me añadido al catálogo canónico y a sus salidas generadas. | Resolución única por launcher del hub y router de biblioteca, desde una distribución reubicada. |

**Pruebas reproducibles**

La suite [test_project_skills_regressions.py](../../tests/test_project_skills_regressions.py) contiene 17 casos nuevos. Extrae los bloques de código de la distribución generada; no utiliza una implementación Rust paralela. Las pruebas Rust están en [project_skills_shared_manifest_tests.rs](../../tests/fixtures/project_skills_shared_manifest_tests.rs).

```sh
uv run --locked pytest tests/test_project_skills_regressions.py tests/test_skill_library_convergence.py tests/test_skill_intent_routing.py tests/test_skill_maintenance.py tests/test_skill_links.py -q
```

Resultado observado: **72 passed**. Incluye generación reproducible, rutas, rollback, conservación de cambios posteriores y portabilidad, además de los nuevos contraejemplos. Tras reconciliar las dos reglas de thermo-audit se repite la comprobación de convergencia de la distribución.

El helper `make_reference_project()` de la suite crea un crate temporal sin dependencias con los bloques exactos del módulo. Sobre ese crate se ejecutó:

```sh
MIRIFLAGS='-Zmiri-strict-provenance' cargo +nightly miri test --locked --offline --manifest-path <directorio-temporal>/Cargo.toml
```

Resultado: **7 pruebas Rust superadas** (6 de estado/concurrencia y 1 de intercalado en el commit). El caso nativo recorre 20.000 publicaciones y cuatro lectores; Miri usa una carga reducida. No son benchmarks ni una prueba exhaustiva de todos los intercalados.

**Distribución y preservación**

Se editó `tools/skill_library/workspace` y el catálogo; la herramienta [maintain_skill_library.py](../../scripts/c5_skills_ontology/maintain_skill_library.py) regeneró únicamente `.agents/skills`, conservando respaldos y recibos fuera del árbol del proyecto. Las 26 entradas pasan estructura, rutas, enlaces locales, patrones semánticos y comparación de hashes de distribución. Las instalaciones globales de skills no se actualizaron.

El workspace tenía cambios previos y actividad concurrente fuera del alcance. No se escribieron ni revirtieron esos archivos; tampoco se modificaron dependencias o lockfiles del proyecto. F08, F10 y apple-bypass conservan los hashes iniciales. La única divergencia previa entre módulos canónicos y distribuidos era thermo-audit; sus dos reglas locales se mantienen en ambas copias.

**Límites de los validadores**

El `quick_validate.py` genérico de skill-creator rechaza los campos ya existentes `role`, `allowed_roles`, `directives`, `display_name` y `canonical_alias`. Se conserva este resultado como incompatibilidad de esquemas; no se eliminan contratos del proyecto para obtener un pase. El validador declarativo propio admite y comprueba esos campos.

Los controles de cierre son `audit_semantic_contracts.py --workspace-only`, `audit_token_budget.py --workspace-only --skip-ghost-listeners` y `verify_active_topology.py`. El alcance omite configuración global, listeners de conversaciones, CI remoto, telemetría y runtime. No se ejecutaron biometría, purgas, despliegues ni servicios.
