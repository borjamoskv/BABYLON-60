<!-- C5-REAL EXERGY CERTIFIED -->
# ESTRUCTURA MAESTRA DEL TEOREMA DE ROBINSON-MOSKV (C5-REAL ABSOLUTE CORE)

Esta es la arquitectura final de extrema exergía del proyecto. Tras una operación de purga termodinámica, el repositorio ha quedado reducido y enfocado **exclusivamente** en soportar los 2 ejes fundamentales del sistema: **CORTEX-PERSIST** y **BABYLON60**. Todo proyecto satélite, forja, OSINT o interfaz secundaria ha sido archivado.

---

## 🏛️ Topología del Repositorio (Doble Eje)

```
Teorema-Robinson-Moskv/
├── BABYLON-60 -> 1_Operaciones_Activas/02_CORTEX_ENGINE/BABYLON-60 (Symlink)
├── cortex-engine -> 1_Operaciones_Activas/02_CORTEX_ENGINE (Symlink)
│
├── 0_Buzon_Entrada/             # Entradas temporales y payloads entrantes (efímero)
├── 1_Operaciones_Activas/
│   └── 02_CORTEX_ENGINE/        # Único Dominio Maestro Superviviente
│       ├── BABYLON-60/          # Frontend de Ejecución C5-REAL (React/TypeScript/Vite)
│       ├── cortex-persist/      # Memoria Determinista C5-REAL
│       ├── cortexpersist-monorepo/
│       └── cortex/              # BFT Orchestrator, Quad-Pillar Kernel (Python 3.12)
│
├── 2_Nucleo_Estatico/           # Anclajes Teóricos (Axiomas, Ontología, Documentación Base)
└── 3_Historico_Inerte/          # Cementerio de Anergía (Proyectos archivados, Logs, OSINT, etc.)
```

---

## 🚀 Puertos de Entrada C5-REAL

La superficie de operaciones se limita a:

1. **`cortex/`**: Núcleo principal de Python. Responsable del orquestador BFT y las simulaciones C5-REAL.
2. **`BABYLON-60/`**: Interfaz de despliegue ideada para interactuar sin teatro (anti-green-theater).
3. **`cortex-persist/`**: Estructuras físicas del ledger y bases de conocimiento inmutable.
