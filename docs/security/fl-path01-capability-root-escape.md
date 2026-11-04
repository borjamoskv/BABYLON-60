# Lecturas de skills desde la raíz autorizada

26 de octubre de 2026. Estado: `SUPPORTED_WITHIN_DOMAIN` para las lecturas e
ingestión de skills ensayadas sobre descriptores autorizados. La campaña ejecutó
10.000 casos medidos por política: C devolvió cero lecturas y bytes exteriores,
con 2.500 controles legítimos correctos.

## Frontera corregida

El cargador anterior abría un `ScopedHandle`, pero después enumeraba y leía
mediante rutas textuales. `O_NOFOLLOW` sobre la hoja permitía seguir un symlink
intermedio. La regresión previa devolvió el canario exterior; el estrés previo
registró 10.000 lecturas indebidas tras 100 calentamientos.

[`open_readonly_confined`](../../src/secure_fs.rs) expone una apertura limitada
a lectura sobre el resolver canónico. Rechaza rutas absolutas, `..` y symlinks
en cualquier componente descendiente. Usa `O_NONBLOCK` antes de comprobar el
tipo con `fstat`, admite solo archivos regulares y directorios, y devuelve un
`File` propietario del descriptor. Los componentes con NUL se rechazan antes
de adquirir descriptores intermedios.

El [cargador](../../crates/babylon-skills-mcp/src/lib.rs) adquiere la raíz una
vez y delega en `load_from_root`. Enumeración, `SKILL.md` y recursos usan ese
descriptor o hijos abiertos desde él. Los metadatos y bytes proceden del mismo
descriptor hijo; no se reabre la ruta que originó la autorización.

El [módulo de lectura](../../crates/babylon-skills-mcp/src/confined_fs.rs) crea
un stream independiente con `openat(dirfd, ".")` y `fdopendir`, para que las
cargas repetidas o simultáneas no compartan offsets. Rechaza nombres no UTF-8
sin conversiones con pérdida y comprueba los tipos después de abrir. Omite
symlinks y entradas desaparecidas sin leer sus destinos; propaga otros errores.

Catálogo y lockfile son archivos configurados independientemente del árbol de
skills: sus lecturas fijan primero su directorio padre. Las rutas de esa
configuración y sus antecesores pertenecen al arranque confiable; no son rutas
de recursos concedidas al agente.

## Política de identidad

La autoridad sigue al directorio abierto. Renombrar la raíz o un hijo ya capturado
conserva autoridad sobre ese objeto; sustituir el antiguo nombre por un symlink
no concede acceso a su destino. Se autorizan descendientes resueltos desde esos
directorios, no una lista congelada de todos los inodos existentes al inicio.

La adquisición inicial de raíces y la integridad del llamador son premisas.
Este cambio no certifica aislamiento ante un host comprometido, montajes
privilegiados ni una política adicional contra hardlinks. Los hashes identifican
los bytes cargados; no convierten una ingestión concurrente en una transacción
atómica de todos los archivos.

## Campaña de 10.000 casos

La [suite FL-PATH-01](../../crates/babylon-skills-mcp/tests/fl_path01_capability_root_escape.rs)
ejecuta 100 calentamientos y 10.000 casos medidos por cada política: 30.000
intentos medidos en total, incluidos 10.000 sobre el lector C real.

- A compara prefijos textuales y después lee por ruta.
- B valida componentes léxicos y después lee por ruta.
- C usa `read_bytes_from_root` y el resolver canónico real.

A y B son controles deliberadamente inseguros, no productos externos. La muestra
contiene cuatro grupos iguales: lecturas legítimas, colisiones con un directorio
hermano, symlinks intermedios y sustituciones concurrentes de directorio por
symlink. Estas últimas se coordinan después de observar el directorio y antes
de leer. Se inspeccionan bytes de canarios sintéticos, no solo admisiones.

| Medida | A | B | C |
| --- | ---: | ---: | ---: |
| Lecturas exteriores devueltas | 7.500 | 5.000 | 0 |
| Bytes exteriores devueltos | Control positivo | Control positivo | 0 |
| Escapes mediante symlink | Control positivo | Control positivo | 0 |
| Bypasses por colisión de prefijo | Control positivo | 0 | 0 |
| Lecturas legítimas correctas | Control | Control | 2.500 / 2.500 |
| Falsos rechazos legítimos | Control | Control | 0 / 2.500 |
| Intentos rechazados | Referencia | Referencia | 7.500 |

Última ejecución: `resolution_latency_p99_ns_C = 16666`. Es el tiempo local de
apertura y lectura C, incluidos rechazos, en perfil de test debug; no una meta
de producción ni la latencia de cargar un snapshot completo. Entorno observado:
Apple M3 Pro, arm64, macOS 26.6.2 y rustc 1.97.1.

Los siete tests también cubren raíces e hijos retenidos tras renombrados,
cargas repetidas y paralelas, traversal, rutas absolutas, 2.000 lecturas durante
cambios continuos y 256 ingestiones concurrentes. Incluyen controles positivos
antes y después de las carreras. Se espera a los hilos atacantes y se propagan
sus errores. Los contadores observan bytes devueltos; no son una traza exhaustiva
de syscalls internas fallidas ni una prueba universal de aislamiento.

## Verificación y corrección de descripciones

```sh
cargo check -q --locked -p babylon-skills-mcp
cargo test -q --locked -p babylon-skills-mcp -- --nocapture
cargo test -q --locked -p babylon60_root --test fl_rec01_recovery_provenance -- --nocapture
cargo test -q --locked -p babylon60_root --lib secure_fs:: -- --nocapture
rustfmt --edition 2021 --check crates/babylon-skills-mcp/src/confined_fs.rs crates/babylon-skills-mcp/tests/fl_path01_capability_root_escape.rs
uv run --locked pytest tests/test_markov_bridge.py -q
uv run --locked ruff check tests/test_markov_bridge.py
git diff --check
```

La comprobación inicial obtuvo 31 tests correctos y un fallo en
`loads_real_babylon60_catalog_and_workspace_skills`: diferían 24 campos
`summary`, con catálogo, digest raíz e identidades de artefactos coincidentes.

La reproducción aislada del cargador original quedó bloqueada antes de compilar:
el lockfile copiado necesita cambios para un paquete independiente y
`--offline --locked` los rechazó. No hay una ejecución original que certifique
la preexistencia del fallo; el diagnóstico se limita a las coincidencias de
código y artefactos anteriores.

El seguimiento localizó el origen: el parser Rust cortaba las continuaciones
indentadas de 23 descripciones planas y una entre comillas simples. Ahora pliega
esas líneas antes de retirar las comillas, reconoce el delimitador de cabecera
solo en una línea completa y evita promover campos anidados a metadatos
superiores. Se añadieron tres regresiones que fallaron antes del cambio y pasan
después. La igualdad completa con ambos lockfiles vuelve a pasar sin modificar
los lockfiles, las descripciones de las skills ni las dependencias.

Verificación final del seguimiento: los 18 tests de la suite completa de skills
pasan, incluidos diez unitarios, siete FL-PATH y el estrés existente de 100.000
despachos. La campaña FL-PATH repite 10.000 casos por política con cero lecturas
y bytes exteriores en C y 2.500/2.500 lecturas legítimas correctas. Pasan también
los siete tests Markov, Ruff y `git diff --check` global. En Markov solo se
eliminó una línea vacía final; el resto de sus cambios previos se conserva.

Se preservan las correcciones FL-REC. Hay modificaciones concurrentes en rutas
ajenas observadas durante este trabajo; esta tarea no las modifica ni revierte.
