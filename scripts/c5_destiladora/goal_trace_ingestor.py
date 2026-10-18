#!/usr/bin/env python3
"""
goal_trace_ingestor.py
======================
Ingestor determinista de trazas operativas de contratos /goal de Antigravity
hacia el Ledger L0 de CORTEX en BABYLON-60.

Parte de la Destiladora L0-Trace-to-Rust.
Autor: Borja Fernández Angulo (borjamoskv)
"""

import sys
import json
import sqlite3
import hashlib
import uuid
from pathlib import Path
from typing import Dict, Any, List

REPO_ROOT = Path(__file__).absolute().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "data/cortex_memory.db"
SCHEMA_PATH = REPO_ROOT / "scripts/c5_destiladora/destiladora_schema.sql"

def ensure_schema(conn: sqlite3.Connection):
    """Garantiza que las tablas de la Destiladora existan en SQLite L0."""
    if SCHEMA_PATH.exists():
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    conn.commit()

def calculate_sha256(data: str) -> str:
    """Calcula hash SHA-256 inmutable de un payload de texto."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def ingest_goal_trace(
    conversation_id: str,
    contract_text: str,
    model_assigned: str,
    thinking_level: str,
    files_touched: List[str],
    tool_sequence: List[Dict[str, Any]],
    output_diff: str,
    exit_gate_cmd: str,
    exit_gate_code: int,
    usage_metadata: Dict[str, Any],
    latency_ms: float,
    db_path: Path = DEFAULT_DB_PATH,
) -> str:
    """
    Registra una traza de contrato resuelto en el Ledger L0.
    Retorna el trace_id (UUID-v4) generado.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    ensure_schema(conn)

    trace_id = str(uuid.uuid4())
    goal_contract_hash = calculate_sha256(contract_text)
    
    # Hash de contexto de entrada
    ast_inputs_combined = "".join(files_touched) + contract_text
    input_ast_digest = calculate_sha256(ast_inputs_combined)
    output_diff_digest = calculate_sha256(output_diff)

    prefill_tokens = usage_metadata.get("prompt_token_count", 0)
    cached_tokens = usage_metadata.get("cached_content_token_count", 0)
    thinking_tokens = usage_metadata.get("thoughts_token_count", 0)
    output_tokens = usage_metadata.get("candidates_token_count", 0)

    with conn:
        conn.execute(
            """
            INSERT INTO cortex_goal_traces (
                trace_id, conversation_id, goal_contract_hash, model_assigned,
                thinking_level, input_ast_digest, files_touched_json,
                tool_sequence_json, output_diff_digest, exit_gate_cmd,
                exit_gate_code, prefill_tokens, cached_tokens, thinking_tokens,
                output_tokens, latency_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_id,
                conversation_id,
                goal_contract_hash,
                model_assigned,
                thinking_level,
                input_ast_digest,
                json.dumps(files_touched),
                json.dumps(tool_sequence),
                output_diff_digest,
                exit_gate_cmd,
                exit_gate_code,
                prefill_tokens,
                cached_tokens,
                thinking_tokens,
                output_tokens,
                latency_ms,
            ),
        )

        # Actualizar o crear cluster de similitud estructural
        cluster_id = calculate_sha256(f"{input_ast_digest}:{exit_gate_cmd}")[:16]
        conn.execute(
            """
            INSERT INTO cortex_invariant_clusters (cluster_id, ast_signature, sample_count, status)
            VALUES (?, ?, 1, 'ACCUMULATING')
            ON CONFLICT(cluster_id) DO UPDATE SET
                sample_count = sample_count + 1
            """,
            (cluster_id, input_ast_digest),
        )

    conn.close()
    return trace_id

if __name__ == "__main__":
    print("🔬 [CORTEX L0 INGESTOR] Módulo de captura listo para integración con Antigravity.")
