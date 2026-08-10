#!/usr/bin/env python3
"""
Proof of Concept (PoC): Operational Worker with Causal Human-in-the-Loop (HITL) Gate
Conforme a RULE[human_in_the_loop_causal_governance] en AGENTS.md.

Demonstrates:
1. ReAct operational execution loop (Plan -> Read Record -> Tool Call -> State Transduction).
2. Non-blocking state snapshotting and Pause/Resume causal gate:
   State_{t+1} = F(State_t, a_t) if a_t NOT IN A_critical OR G_human(a_t) == APPROVED
   State_{t+1} = PAUSED(State_t, a_t) if a_t IN A_critical AND G_human(a_t) == PENDING
3. Multidisciplinary domain mapping (Business CRM, Code Security Audit, Audiovisual Rendering).
"""

import enum
import json
import os
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional


class ActionCriticality(enum.Enum):
    READ_ONLY = "READ_ONLY"      # Non-mutative (e.g. read record, parse AST, fetch metadata)
    COMPUTATIONAL = "COMPUTE"   # Reversible computation (e.g. simulation, transcode draft)
    MUTATIVE_CRITICAL = "CRITICAL" # High-impact mutation (e.g. DB commit, deploy script, push)


class AgentState(enum.Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED_AWAITING_SIGN_OFF = "PAUSED_AWAITING_SIGN_OFF"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"


class CausalHitlEngine:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        with self._conn as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS state_snapshots (
                    execution_id TEXT PRIMARY KEY,
                    domain TEXT NOT NULL,
                    current_step INTEGER NOT NULL,
                    state_status TEXT NOT NULL,
                    pending_action TEXT,
                    payload JSON NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    criticality TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            conn.commit()

    def save_snapshot(self, execution_id: str, domain: str, step: int, status: AgentState,
                      pending_action: Optional[str], payload: Dict[str, Any]):
        now = time.time()
        with self._conn as conn:
            conn.execute("""
                INSERT INTO state_snapshots (execution_id, domain, current_step, state_status, pending_action, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(execution_id) DO UPDATE SET
                    current_step=excluded.current_step,
                    state_status=excluded.state_status,
                    pending_action=excluded.pending_action,
                    payload=excluded.payload,
                    updated_at=excluded.updated_at
            """, (execution_id, domain, step, status.value, pending_action, json.dumps(payload), now, now))
            conn.commit()

    def record_decision(self, execution_id: str, action_name: str, criticality: ActionCriticality, decision: str):
        with self._conn as conn:
            conn.execute("""
                INSERT INTO audit_ledger (execution_id, action_name, criticality, decision, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (execution_id, action_name, criticality.value, decision, time.time()))
            conn.commit()

    def load_snapshot(self, execution_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        cur.execute("SELECT domain, current_step, state_status, pending_action, payload FROM state_snapshots WHERE execution_id=?", (execution_id,))
        row = cur.fetchone()
        if row:
            return {
                "domain": row[0],
                "current_step": row[1],
                "status": AgentState(row[2]),
                "pending_action": row[3],
                "payload": json.loads(row[4])
            }
        return None


class OperationalWorkerPoC:
    def __init__(self, execution_id: str, domain: str, engine: CausalHitlEngine):
        self.execution_id = execution_id
        self.domain = domain
        self.engine = engine

    def execute_plan(self, steps: List[Dict[str, Any]], auto_approve_prompt: bool = True):
        print(f"\n[🚀 START] Starting Execution [{self.execution_id}] in Domain: [{self.domain}]")
        
        snapshot = self.engine.load_snapshot(self.execution_id)
        start_step = snapshot["current_step"] if snapshot else 0
        payload = snapshot["payload"] if snapshot else {"logs": []}

        for idx in range(start_step, len(steps)):
            step_info = steps[idx]
            action_name = step_info["action"]
            criticality = step_info["criticality"]
            func = step_info["func"]

            print(f" -> Step {idx + 1}/{len(steps)}: Running [{action_name}] (Criticality: {criticality.value})")

            # Evaluate Causal Gate
            if criticality == ActionCriticality.MUTATIVE_CRITICAL:
                print(f"\n[⚠️ CAUSAL GATE] Action [{action_name}] requires HUMAN SIGN-OFF!")
                self.engine.save_snapshot(
                    self.execution_id, self.domain, idx,
                    AgentState.PAUSED_AWAITING_SIGN_OFF, action_name, payload
                )

                if auto_approve_prompt:
                    decision = "APPROVED"
                    print(f" [HUMAN SIGN-OFF] Simulated Human Approval: >>> {decision} <<<")
                else:
                    decision = "PENDING"
                    print(" [HUMAN SIGN-OFF] Paused execution. Waiting for async sign-off...")
                    return

                self.engine.record_decision(self.execution_id, action_name, criticality, decision)

                if decision != "APPROVED":
                    self.engine.save_snapshot(
                        self.execution_id, self.domain, idx,
                        AgentState.REJECTED, action_name, payload
                    )
                    print(f"[❌ ABORTED] Action [{action_name}] rejected by Human Sign-off.")
                    return

            # Execute Tool Action
            result = func(payload)
            payload["logs"].append(f"Step {idx + 1} ({action_name}): {result}")
            print(f"   ✓ Tool Executed: {result}")

            # Save state after step completion
            self.engine.save_snapshot(
                self.execution_id, self.domain, idx + 1,
                AgentState.RUNNING if idx + 1 < len(steps) else AgentState.COMPLETED,
                None, payload
            )

        print(f"\n[✅ SUCCESS] Execution [{self.execution_id}] completed successfully.")


# Domain Tool Implementations
def tool_read_records(payload):
    return "Fetched 14 active records from SQLite memory buffer"

def tool_audit_dependencies(payload):
    return "Scan clean: 0 hallucinated imports detected in codebase"

def tool_render_preview(payload):
    return "Rendered 1080p preview frame sequence via Remotion pipeline"

def tool_commit_to_production(payload):
    return "Mutated state: Published release artifact & triggered deployment workflow"


def main():
    print("=" * 80)
    print("   C5-REAL / BABYLON-60: Operational Worker & Causal HITL Gate (PoC)")
    print("=" * 80)

    engine = CausalHitlEngine()

    # Define Workflow Steps
    workflow_steps = [
        {
            "action": "Ingest_And_Parse_Data",
            "criticality": ActionCriticality.READ_ONLY,
            "func": tool_read_records
        },
        {
            "action": "Execute_Security_Audit",
            "criticality": ActionCriticality.COMPUTATIONAL,
            "func": tool_audit_dependencies
        },
        {
            "action": "Generate_Media_Preview",
            "criticality": ActionCriticality.COMPUTATIONAL,
            "func": tool_render_preview
        },
        {
            "action": "Commit_And_Deploy_Production",
            "criticality": ActionCriticality.MUTATIVE_CRITICAL,
            "func": tool_commit_to_production
        }
    ]

    # Run PoC for Domain 1: Audiovisual & Code Swarm Orchestration
    worker = OperationalWorkerPoC(
        execution_id="EXEC-2026-0810-POC",
        domain="Multidisciplinary_Swarm_Orchestration",
        engine=engine
    )

    worker.execute_plan(workflow_steps, auto_approve_prompt=True)

    # Inspect Audit Ledger
    cur = engine._conn.cursor()
    cur.execute("SELECT execution_id, action_name, criticality, decision, timestamp FROM audit_ledger")
    rows = cur.fetchall()
    print("\n" + "=" * 80)
    print("   AUDIT LEDGER SNAPSHOT (Causal Gate Approvals)")
    print("=" * 80)
    for r in rows:
        print(f" Execution: {r[0]} | Action: {r[1]} | Level: {r[2]} | Decision: {r[3]}")
    print("=" * 80)


if __name__ == "__main__":
    main()
