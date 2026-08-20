# apps/ — Aplicaciones BABYLON-60

Directorio de aplicaciones del ecosistema. Cada subdirectorio es una aplicación independiente con su propio toolchain.

## Arquitectura de Conjunto

```
apps/
├── babylon60-ide/   ← IDE soberano (Tauri + Node + Python backend)
├── tonnetz_app/     ← Visualizador de redes Tonnetz para auditoría armónica
└── web/             ← Aplicación web principal (Vite/React + Cloudflare Workers)
```

## Tabla de Aplicaciones

| App | Tecnología | Propósito | Entry Point |
|---|---|---|---|
| [`babylon60-ide/`](./babylon60-ide/) | Tauri (Rust) + Node.js + Python | IDE soberano con integración MCP nativa y enjambres | `apps/babylon60-ide/package.json` |
| [`tonnetz_app/`](./tonnetz_app/) | HTML/JS/CSS | Visualizador interactivo de redes Tonnetz y auditoría armónica | `apps/tonnetz_app/index.html` |
| [`web/`](./web/) | Vite + React + TypeScript | Frontend web principal con núcleo Rust compilado a WASM | `apps/web/package.json` |
| [`src-tauri/`](./src-tauri/) | Rust/Tauri | Shell nativo compartido para `babylon60-ide` | `apps/src-tauri/Cargo.toml` |

## Relaciones

- `web/rust-core/` → compila el núcleo matemático Rust a WASM para uso en el browser.
- `babylon60-ide/` → conecta con el servidor MCP Python en `packages/babylon60/mcp/cortex_mcp_server.py`.
- `tonnetz_app/` → consume las primitivas de `packages/babylon60/primitives/tonnetz_monitor.py`.

## Comandos

```bash
# Web app
cd apps/web && npm run dev

# IDE
cd apps/babylon60-ide && npm run dev

# Tonnetz (local)
open apps/tonnetz_app/index.html
```
