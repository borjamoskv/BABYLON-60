# 🗄️ Data — Repositorios de Persistencia y Atestación

> **DOMINIO DE ALMACENAMIENTO (L1/L2 Sink)**  
> Ubicación: `data/`  
> Invariante: **Inmutabilidad Causal / Append-Only**

El directorio de datos es el ancla epistémica del proyecto BABYLON-60. Solo almacena registros inmutables, SQLite de lectura-escritura transaccional C5-REAL, telemetría térmica y metadatos forenses. Todo archivo dinámico debe purgarse mediante el motor de anergía si es efímero.

## 📐 Estructura de Persistencia

| Artefacto / Directorio | Propósito Funcional |
|---|---|
| `logs/` | Sink principal de registros inmutables (Append-Only) y telemetría de agentes. |
| `cortex.db`, `cortex_memory.db` | Lentes Bayesianas y memoria episódica consolidada de los agentes cognitivos. |
| `cib_master_ledger.db` / `cib_async_ledger.db` | CIB Ledgers. Topología transaccional de estados base y asíncronos. |
| `oncology_300.json` / `shards.json` | Cargas de datos de frontera. Matrices de protocolo de oncología simulada y sharding. |
| `artifact_bundle_v3/` | Paquetes de atestación firmados (RFC 9942 COSE_Sign1) y recibos de estado. |
| `L1_sink/` | Persistencia lenta y definitiva. Anclaje de datos que no requiere acceso cache-line. |

## 🛡️ Reglas Arquitectónicas (C5-REAL)
- **Cero Mutaciones Destructivas (UPDATE/DELETE):** La base de datos es un log transaccional de agregación. 
- **Purga de Anergía:** Los caches, backups intermedios de sqlite (`.db-wal`, `.db-shm`) y bases de datos efímeras huérfanas deben destruirse regularmente invocando `purga anergia`.
