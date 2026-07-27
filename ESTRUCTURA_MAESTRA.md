# ESTRUCTURA MAESTRA DEL TEOREMA DE ROBINSON-MOSKV

Esta es la arquitectura consolidada de produccion del proyecto. Todos los 35+ modulos dispersos han sido asimilados y reestructurados en **4 Dominios Maestros** bajo la capa `1_Operaciones_Activas`.

---

## 🏛️ Estructura de Dominios

```
Teorema-Robinson-Moskv/
├── intel-suite -> 1_Operaciones_Activas/01_INTEL_SUITE (Symlink)
├── cortex-engine -> 1_Operaciones_Activas/02_CORTEX_ENGINE (Symlink)
├── moskv-studio -> 1_Operaciones_Activas/03_MOSKV_STUDIO (Symlink)
├── laboratorio-rd -> 1_Operaciones_Activas/04_LABORATORIO_RD (Symlink)
│
├── 0_Buzon_Entrada/
├── 1_Operaciones_Activas/
│   ├── 01_INTEL_SUITE/          # Producto OSINT & Inteligencia Documental (SaaS/B2B)
│   ├── 02_CORTEX_ENGINE/        # Motor de IA, Memoria Determinista (cortex-persist) y Ultrathink
│   ├── 03_MOSKV_STUDIO/         # App de escritorio (Tauri/Vite) y Forjas de Contenido Multimedia
│   └── 04_LABORATORIO_RD/       # Compilador Moskv84, Simulación y R&D Avanzado
│
├── 2_Nucleo_Estatico/
└── 3_Historico_Inerte/
```

---

## 🚀 Puertos de Entrada Rápidos

1. **`01_INTEL_SUITE/`**: `substack-osint-miner`, `documentary_agent_omega`, `substack-anti-mafia-extension`.
2. **`02_CORTEX_ENGINE/`**: `BABYLON-60` (`ultrathink`), `cortex-persist`, `cortex-routing-bunker`, `cortex_sentinel`.
3. **`03_MOSKV_STUDIO/`**: `src-tauri`, `cortex-web`, `video-forge`, `twin-forge`, `harmony-forge`.
4. **`04_LABORATORIO_RD/`**: `moskv-1-apex`, `moskv84-compiler`, `strike-rs`.
