# `babylon-skills-mcp` (SEP-2640 Read-Only Skills Gateway)

Crate nativo en Rust que implementa la arquitectura **V1** en `BABYLON-60`:

$$\boxed{\text{Catálogo existente} \rightarrow \text{Snapshot verificado en RAM} \rightarrow \text{MCP Read-Only}}$$

## Responsabilidades y Frontera de Privilegios

- **Snapshot Inmutable (`ImmutableSkillsSnapshot`):** Lee `docs/skills.json` y `.agents/skills` al arrancar usando descriptores `O_RDONLY | O_NOFOLLOW` (sin seguir enlaces simbólicos terminales) y sella los hashes `SHA-256` por archivo, por skill y de raíz (`snapshot_root`).
- **Inmunidad TOCTOU:** Las peticiones MCP (`skills/list`, `skills/get`, `resources/read`, `prompts/list`, `prompts/get`) sirven exclusivamente desde la memoria cargada al arranque; nunca leen el sistema de archivos vivo durante las peticiones.
- **Separación de Autoridad (`ΔSkills ⇏ ΔAuthority`):** El servidor de skills es estrictamente de solo lectura. Registrar propuestas de herramientas hacia [`McpCapabilityBroker`](../../src/capability.rs) utiliza únicamente `register_tool` (descubrimiento no confiable); jamás invoca `authorize_tool` ni emite `McpCapabilityToken`.
