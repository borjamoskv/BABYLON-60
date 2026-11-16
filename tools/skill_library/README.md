# Fuente canónica de skills

`catalog.json` es la única fuente de metadatos, aliases, capacidades, intenciones y políticas de selección. `global/`, `codex_overrides/` y `workspace/` conservan los procedimientos y recursos; los frontmatters, índices y launchers de la distribución se generan. No se editan las copias instaladas.

## Generar y verificar

`python3 scripts/c5_skills_ontology/maintain_skill_library.py --target codex=/ruta/codex/skills --target antigravity=/ruta/gemini/config/skills --output /ruta/nueva/release`

Cada destino conserva su variante. Añadir `--target workspace=/ruta/proyecto/.agents/skills` actualiza la salida del proyecto. El directorio de informe debe ser nuevo. Sin `--apply` no se modifica ninguna instalación.

## Distribuir y revertir

El mismo comando con `--apply` genera, comprueba y distribuye las entradas propias. Las copias terminan antes de modificar instalaciones. Cada entrada se sustituye mediante rename local, se conserva su versión anterior y se comparan hashes, modos y referencias tras la instalación. `.system` y los siblings ajenos se conservan. Si falla otro entorno, se restaura lo ya aplicado. Una interrupción se puede revisar con el recibo; no se declara una transacción atómica entre varios directorios.

`python3 scripts/c5_skills_ontology/maintain_skill_library.py --rollback /ruta/release/receipt.json` revierte una distribución sin sobrescribir cambios posteriores del usuario. Conservar los respaldos indicados en el recibo.

## Selección por intención

Los nombres y aliases explícitos siguen disponibles. Las peticiones contextuales requieren acción y tema dentro de la misma cláusula; las negaciones y las citas reportadas se excluyen. Son reglas declaradas, no comprensión semántica general. Un `sigue` aislado no activa ningún módulo; `--context` permite conservar el objetivo anterior cuando el anfitrión lo proporciona. No se ejecutan procedimientos al seleccionar rutas.

`python3 /ruta/skills/_skill_router.py --library-root /ruta/skills --query "Audita mis skills por solapamiento"`

Los hubs conservan `scripts/route.py` como launchers generados de la misma implementación. Un resultado ambiguo devuelve código 3; sin resultado, código 2. Una ruta única devuelve 0.

## Auditoría común, comprobadores independientes

`report.json` conserva resultados separados de estructura declarativa, rutas, recursos heredados, enlaces locales y contratos semánticos. El inventario de hashes verifica la distribución sin sustituir esos controles. Las comprobaciones semánticas son léxicas y sus hallazgos requieren revisión contextual; no miden calidad ni energía. Los enlaces remotos quedan marcados como no verificados cuando no se pide comprobación de red.
