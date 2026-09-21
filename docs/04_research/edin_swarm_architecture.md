# ⚡ Arquitectura Edin Swarm (`scripts/edin_swarm_runner.py`)
[![Swarm Size](https://img.shields.io/badge/Swarm-100_ULTRATHINK_Agents-orange?style=for-the-badge)]()
[![Disk Overhead](https://img.shields.io/badge/Worktree_Overhead-0_Disk_Overhead-brightgreen?style=for-the-badge)]()
[![BFT Ledger](https://img.shields.io/badge/Ledger-BFTLedgerActor_Commit-purple?style=for-the-badge)](../../babylon60/bft/README.md)

La **Arquitectura Edin Swarm** es el sistema de mapeo e inspección masiva de superficies de código para **BABYLON-60**.

---

## 🏗️ Fases del Enjambre Edin

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Edin Swarm Commander (edin_swarm_commander.py)   │
│ - Mapeo AST de funciones, clases y esquemas DB              │
│ - Cristalización de Shards en scripts/shards.json (436 vecs) │
├─────────────────────────────────────────────────────────────┤
│ 2. Edin Swarm Runner (edin_swarm_runner.py)        │
│ - Ejecución paralela in-memory de 100 Agentes ULTRATHINK    │
│ - Commits asíncronos en BFTLedgerActor (cib_async_ledger.db)│
├─────────────────────────────────────────────────────────────┤
│ 3. Notariado Causal Determinista                           │
│ - Cero sobrecoste de disco (0 Worktree Overhead)            │
│ - 100% Attestation BFT con hashes idempotentes UUIDv5        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 Mecanismo de Idempotencia y Causal Taint

Cada agente ULTRATHINK genera una clave de idempotencia determinista basada en el espacio de nombres DNS y el target del vector:

```python
idempotency_key = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{agent_name}:{target}"))

event = LedgerEvent(
    stream="edin_swarm",
    entity_id=idempotency_key,
    event_type="VECTOR_AUDIT_COMPLETED",
    payload={"agent": agent_name, "status": "C5_VERIFIED"},
    cortex_taint=f"{agent_name}:edin_swarm_runner",
    source_db="cib_async_ledger.db",
)
```

---

## ⚡ Ejecución CLI

```bash
# 1. Extraer vectores AST y cristalizar Shards
python3 scripts/edin_swarm_commander.py

# 2. Ejecutar la auditoría masiva de 100 Agentes ULTRATHINK en paralelo
python3 scripts/edin_swarm_runner.py
```

---

<sub>BABYLON-60 Edin Swarm · 100 Agentes ULTRATHINK In-Memory · Borja Moskv</sub>
