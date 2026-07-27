# Ejemplo Completo de Ciclo L0→L6 (BABYLON-60 Audit Protocol)

Este documento ilustra un ciclo completo de ingeniería causal en formato JSON ejecutable, basado en la resolución de una colisión de concurrencia en la base de datos `cortex.db`.

---

## [L0] EVIDENCE: Captura de Error de Bloqueo
*Fichero: `schema/evidence.schema.json`*

```json
{
  "evidence_id": "f81d4fae-7dec-11d0-a765-00a0c91e6bf6",
  "source_type": "LOG_FILE",
  "payload": "sqlite3.OperationalError: database is locked during concurrent write in thread pool worker-2",
  "timestamp": "2026-06-29T19:05:00Z",
  "cortex_taint_hash": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
}
```

---

## [L1] PATTERN EXTRACTION: Invariante Estructural
*Fichero: `schema/pattern.schema.json`*

```json
{
  "pattern_id": "8482b6b0-ec18-40d1-9488-294b0d0ad211",
  "evidence_ids": ["f81d4fae-7dec-11d0-a765-00a0c91e6bf6"],
  "invariant_claim": "The database lock occurs exclusively during write concurrency when journal_mode is set to DELETE instead of WAL.",
  "shannon_entropy_score": 0.85
}
```

---

## [L2] COGNITIVE MODEL: Grafo Causal
*Fichero: `schema/model.schema.json`*

```json
{
  "model_id": "2d8f99e4-c5a4-4f0e-b7d1-3ab98d8ee27e",
  "pattern_ids": ["8482b6b0-ec18-40d1-9488-294b0d0ad211"],
  "causal_graph": {
    "nodes": {
      "A": "journal_mode = DELETE",
      "B": "Concurrent write transactions",
      "C": "Deadlock (database is locked)"
    },
    "edges": [
      { "from": "A", "to": "C", "relation": "exacerbates_locking_contention" },
      { "from": "B", "to": "C", "relation": "triggers_contention" }
    ]
  },
  "confidence_level": "HIGH"
}
```

---

## [L3] PREDICTION: Aserción Falsable
*Fichero: `schema/prediction.schema.json`*

```json
{
  "prediction_id": "7ca6470b-689e-4ff6-8c43-bdf5df84b8ae",
  "model_id": "2d8f99e4-c5a4-4f0e-b7d1-3ab98d8ee27e",
  "falsifiable_condition": "Running a concurrent write benchmark with journal_mode=WAL will result in 0% OperationalError drops over 1000 transactions.",
  "experiment_design": {
    "setup_saga": "Initialize local memory DB shard with journal_mode=WAL.",
    "execution_trigger": "Spawn 10 parallel threads executing mock mutations.",
    "success_criteria": "Error rate == 0"
  },
  "experiment_result": "PENDING"
}
```

---

## [L4] EXPERIMENT: Ejecución en Sandbox Aislado
*Fichero: `schema/experiment.schema.json`*

```json
{
  "experiment_id": "90e3df2f-7c1b-4b13-8d0f-488cb9958045",
  "prediction_id": "7ca6470b-689e-4ff6-8c43-bdf5df84b8ae",
  "execution_context": "SANDBOX_THREAD",
  "outcome": {
    "refuted": false,
    "evidence_hash": "c9a8b7d6e5f4c3b2a10d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b"
  }
}
```

---

## [L5] INTERVENTION: Mutación Física
*Fichero: `schema/intervention.schema.json`*

```json
{
  "intervention_id": "60a4f51e-d4c3-4b92-800a-200b300c400d",
  "prediction_id": "7ca6470b-689e-4ff6-8c43-bdf5df84b8ae",
  "git_sentinel_hash": "dcba2835f",
  "saga_rollback_plan": "Execute PRAGMA journal_mode=DELETE; on next database boot sequence.",
  "l6_reevaluation_status": "PENDING"
}
```

---

## [L6] RE-EVALUATION: Cierre de Bucle
*Fichero: `schema/intervention.schema.json` (actualizado)*

```json
{
  "intervention_id": "60a4f51e-d4c3-4b92-800a-200b300c400d",
  "prediction_id": "7ca6470b-689e-4ff6-8c43-bdf5df84b8ae",
  "git_sentinel_hash": "dcba2835f",
  "saga_rollback_plan": "Execute PRAGMA journal_mode=DELETE; on next database boot sequence.",
  "l6_reevaluation_status": "RESOLVED"
}
```
*(Nota: El sistema re-escanea los logs y confirma un ratio de colisiones de 0% en producción).*
