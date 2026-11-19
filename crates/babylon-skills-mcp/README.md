# `babylon-skills-mcp` (SEP-2640 Read-Only Skills Gateway)

Crate nativo en Rust que implementa la arquitectura **V1** en `BABYLON-60`:

$$\boxed{\text{Catálogo existente} \rightarrow \text{Snapshot verificado en RAM} \rightarrow \text{MCP Read-Only}}$$

## Responsabilidades y Frontera de Privilegios

- **Snapshot Inmutable (`ImmutableSkillsSnapshot`):** Lee `docs/skills.json` y `.agents/skills` al arrancar usando descriptores `O_RDONLY | O_NOFOLLOW` (sin seguir enlaces simbólicos terminales) y sella los hashes `SHA-256` por archivo, por skill y de raíz (`snapshot_root`).
- **Inmunidad TOCTOU:** Las peticiones MCP (`skills/list`, `skills/get`, `resources/read`, `prompts/list`, `prompts/get`) sirven exclusivamente desde la memoria cargada al arranque; nunca leen el sistema de archivos vivo durante las peticiones.
- **Separación de Autoridad (`ΔSkills ⇏ ΔAuthority`):** El servidor de skills es estrictamente de solo lectura. Registrar propuestas de herramientas hacia [`McpCapabilityBroker`](../../src/capability.rs) utiliza únicamente `register_tool` (descubrimiento no confiable); jamás invoca `authorize_tool` ni emite `McpCapabilityToken`.

## Anclaje de artefactos (FL-P08 v3.2)

Esquema de lock `3.2.0`. Un lock `3.1.0`, o uno sin `artifact_provenance` o `lock_scope`, se rechaza sin valor por defecto.

| `artifact_provenance` | Qué sella `artifact_sha256` | Lock |
| --- | --- | --- |
| `workspace_disk` | Recursos físicos bajo `.agents/skills/<id>/` | `skills-lock.json` |
| `catalog_synthetic` | Texto derivado de los metadatos de `docs/skills.json`; no cubre ningún fichero | `skills-lock.json` |
| `global_disk` | Recursos físicos bajo una raíz `--global-skills-dir` | lock global del operador |

- **I1:** la procedencia forma parte de `tool_identity_hash` (`v3.2:<id>@<versión>:<sha>:<procedencia>:<clase>`).
- **I2:** un mismo nombre de skill en varias raíces aborta la carga con `DUPLICATE_SKILL_ARTIFACT`.
- **I3:** las raíces globales se recorren con la misma disciplina `openat | O_NOFOLLOW`.
- **I4:** `skills-lock.json` no depende de las raíces globales; CI lo regenera de forma idéntica.
- **I5:** `skills.propose_effect` deniega `DESTRUCTIVE`, `STATE_MUTATION` y `READ_EXT` sin artefacto físico sellado (`ARTIFACT_UNBOUND`).

El gemelo Python (`01_KISH_ENGINE/babylon60/mcp/skills_snapshot.py`) aplica el mismo esquema e I5 sobre la capa de repositorio; no carga raíces globales.

```bash
# Regenerar el lock del repositorio (mantenimiento explícito)
babylon-skills-mcp --emit-lockfile skills-lock.json
# Sellar raíces globales (lock local del operador, fuera del repositorio)
babylon-skills-mcp --global-skills-dir <dir> --emit-global-lockfile <skills-lock.global.json>
# Arranque con ambas capas; sin --global-lockfile sale con GLOBAL_LOCK_REQUIRED
babylon-skills-mcp --global-skills-dir <dir> --global-lockfile <skills-lock.global.json>
```
