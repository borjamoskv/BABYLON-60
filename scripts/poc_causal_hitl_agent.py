#!/usr/bin/env python3
"""
SOTA Proof of Concept (PoC): Operational Worker with Cryptographic Causal HITL Gate
Conforme a RULE[human_in_the_loop_causal_governance] y RULE[c5_real_invariants] en AGENTS.md.

Demonstrates:
1. ReAct operational execution loop (Plan -> Read Record -> Tool Call -> State Transduction).
2. Asynchronous State Suspension & Resumption via Causal Gate (Human Sign-off):
   State_{t+1} = F(State_t, a_t) if a_t NOT IN A_critical OR G_human(a_t) == APPROVED
   State_{t+1} = PAUSED(State_t, a_t) if a_t IN A_critical AND G_human(a_t) == PENDING
3. Cryptographic SCITT-compliant SHA-256 Tamper-Evident Audit Ledger.
4. Multidisciplinary Domain Workflows (Business CRM, Code Security Audit, Audiovisual Rendering).
"""

import enum
import hashlib
import json
import os
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional, Tuple


class ActionCriticality(enum.Enum):
    READ_ONLY = "READ_ONLY"          # Non-mutative (e.g. read record, parse AST, fetch metadata)
    COMPUTATIONAL = "COMPUTE"       # Reversible computation (e.g. simulation, transcode draft)
    MUTATIVE_CRITICAL = "CRITICAL"   # High-impact mutation (e.g. DB commit, deploy script, push)


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
                    timestamp REAL NOT NULL,
                    prev_digest TEXT NOT NULL,
                    cryptographic_digest TEXT NOT NULL
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

    def record_decision(self, execution_id: str, action_name: str, criticality: ActionCriticality, decision: str) -> str:
        cur = self._conn.cursor()
        cur.execute("SELECT cryptographic_digest FROM audit_ledger ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        prev_digest = row[0] if row else "0" * 64

        now = time.time()
        raw_data = f"{execution_id}|{action_name}|{criticality.value}|{decision}|{now:.6f}|{prev_digest}"
        digest = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()

        with self._conn as conn:
            conn.execute("""
                INSERT INTO audit_ledger (execution_id, action_name, criticality, decision, timestamp, prev_digest, cryptographic_digest)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (execution_id, action_name, criticality.value, decision, now, prev_digest, digest))
            conn.commit()
        return digest

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

    def verify_ledger_integrity(self) -> bool:
        cur = self._conn.cursor()
        cur.execute("SELECT execution_id, action_name, criticality, decision, timestamp, prev_digest, cryptographic_digest FROM audit_ledger ORDER BY id ASC")
        rows = cur.fetchall()
        expected_prev = "0" * 64
        for r in rows:
            exec_id, action, crit, dec, ts, prev_d, digest = r
            if prev_d != expected_prev:
                return False
            raw_data = f"{exec_id}|{action}|{crit}|{dec}|{ts:.6f}|{prev_d}"
            calc_digest = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
            if calc_digest != digest:
                return False
            expected_prev = digest
        return True


class OperationalWorkerPoC:
    def __init__(self, execution_id: str, domain: str, engine: CausalHitlEngine):
        self.execution_id = execution_id
        self.domain = domain
        self.engine = engine

    def execute_plan(self, steps: List[Dict[str, Any]], auto_approve: bool = True, async_mode: bool = False) -> AgentState:
        print(f"\n" + "═" * 80)
        print(f"   [🚀 START EXECUTION] ID: [{self.execution_id}] | Domain: [{self.domain}]")
        print("═" * 80)
        
        snapshot = self.engine.load_snapshot(self.execution_id)
        start_step = snapshot["current_step"] if snapshot else 0
        payload = snapshot["payload"] if snapshot else {"logs": [], "artifacts": []}

        for idx in range(start_step, len(steps)):
            step_info = steps[idx]
            action_name = step_info["action"]
            criticality = step_info["criticality"]
            func = step_info["func"]

            crit_badge = f"\033[94m[{criticality.value}]\033[0m" if criticality == ActionCriticality.READ_ONLY else (
                f"\033[93m[{criticality.value}]\033[0m" if criticality == ActionCriticality.COMPUTATIONAL else
                f"\033[91m[{criticality.value}]\033[0m"
            )

            print(f" ▶ Step {idx + 1}/{len(steps)}: Action [{action_name}] {crit_badge}")

            # Evaluate Causal Gate
            if criticality == ActionCriticality.MUTATIVE_CRITICAL:
                print(f"\n   \033[91m[⚠️ CAUSAL GATE DETECTED]\033[0m High-impact mutation requested: [{action_name}]")
                self.engine.save_snapshot(
                    self.execution_id, self.domain, idx,
                    AgentState.PAUSED_AWAITING_SIGN_OFF, action_name, payload
                )

                if async_mode:
                    print(f"   \033[93m[⏸️ ASYNC PAUSE]\033[0m Execution suspended safely. State snapshot saved.")
                    print(f"   To resume, invoke: `worker.resume_execution('{self.execution_id}', decision='APPROVED')`\n")
                    return AgentState.PAUSED_AWAITING_SIGN_OFF

                if auto_approve:
                    decision = "APPROVED"
                    print(f"   \033[92m[✓ HUMAN SIGN-OFF]\033[0m Decision received: >>> \033[1m{decision}\033[0m <<<")
                else:
                    decision = "REJECTED"
                    print(f"   \033[91m[✗ HUMAN SIGN-OFF]\033[0m Decision received: >>> \033[1m{decision}\033[0m <<<")

                digest = self.engine.record_decision(self.execution_id, action_name, criticality, decision)
                print(f"   \033[90m[🔐 SHA-256 RECEIPT]\033[0m {digest[:16]}...{digest[-16:]}")

                if decision != "APPROVED":
                    self.engine.save_snapshot(
                        self.execution_id, self.domain, idx,
                        AgentState.REJECTED, action_name, payload
                    )
                    print(f"\n\033[91m[❌ ABORTED]\033[0m Execution [{self.execution_id}] halted by Human Sign-off.")
                    return AgentState.REJECTED

            # Execute Tool Action
            result, artifact = func(payload)
            payload["logs"].append(f"Step {idx + 1} ({action_name}): {result}")
            if artifact:
                payload["artifacts"].append(artifact)
            print(f"   ✓ Executed: {result}")

            # Save state snapshot after step completion
            self.engine.save_snapshot(
                self.execution_id, self.domain, idx + 1,
                AgentState.RUNNING if idx + 1 < len(steps) else AgentState.COMPLETED,
                None, payload
            )

        print(f"\n\033[92m[✅ COMPLETED]\033[0m Workflow [{self.execution_id}] finished with 100% causal integrity.")
        return AgentState.COMPLETED

    def resume_execution(self, decision: str, steps: List[Dict[str, Any]]) -> AgentState:
        snapshot = self.engine.load_snapshot(self.execution_id)
        if not snapshot or snapshot["status"] != AgentState.PAUSED_AWAITING_SIGN_OFF:
            print(f"Error: No paused snapshot found for execution ID [{self.execution_id}].")
            return AgentState.IDLE

        pending_action = snapshot["pending_action"]
        idx = snapshot["current_step"]
        print(f"\n[🔄 RESUMING EXECUTION] ID: [{self.execution_id}] at Step {idx + 1}")
        print(f"   Sign-off Decision for [{pending_action}]: >>> {decision} <<<")

        digest = self.engine.record_decision(self.execution_id, pending_action, ActionCriticality.MUTATIVE_CRITICAL, decision)
        print(f"   [🔐 SHA-256 RECEIPT] {digest[:16]}...{digest[-16:]}")

        if decision != "APPROVED":
            self.engine.save_snapshot(
                self.execution_id, self.domain, idx,
                AgentState.REJECTED, pending_action, snapshot["payload"]
            )
            print(f"[❌ ABORTED] Execution [{self.execution_id}] rejected.")
            return AgentState.REJECTED

        # Execute pending action and continue remaining steps
        return self.execute_plan(steps, auto_approve=True, async_mode=False)


# --- Multidisciplinary Domain Tool Implementations ---

# 1. Business / CRM Workflow Tools
def tool_fetch_crm_leads(payload):
    return "Retrieved 28 inbound business leads from PostgreSQL buffer", {"count": 28}

def tool_qualify_leads(payload):
    return "Score evaluation complete: 12 high-priority leads identified", {"high_priority": 12}

def tool_dispatch_crm_emails(payload):
    return "MUTATION: Triggered automated personalized outreach to 12 leads", {"sent": 12}


# 2. Code Security & Existence-Gap Audit Tools
def tool_scan_ast_imports(payload):
    return "Parsed 142 Python/Rust files. Extracted 890 import statements.", {"files": 142}

def tool_verify_existence_gap(payload):
    return "Existence-Gap Audit clean: 0 phantom dependencies or slopsquatting detected.", {"gaps": 0}

def tool_apply_git_patch(payload):
    return "MUTATION: Applied verified refactoring patch and pushed commit to main", {"commit": "5a773af"}


# 3. Audiovisual & Remotion Pipeline Tools
def tool_parse_remotion_script(payload):
    return "Parsed documentary script into 18 scene timelines", {"scenes": 18}

def tool_render_preview_frames(payload):
    return "Rendered 1080p preview video sequence at 60fps in buffer", {"fps": 60}

def tool_publish_4k_master(payload):
    return "MUTATION: Rendered 4K ProRes master and deployed asset to CDN", {"cdn_url": "https://cdn.babylon60.io/v1/master.mp4"}


def main():
    print("═" * 80)
    print("   C5-REAL / BABYLON-60: SOTA Operational Worker & Causal HITL Engine")
    print("═" * 80)

    engine = CausalHitlEngine()

    # --- Scenario 1: Async Suspension & Resumption (Business CRM Domain) ---
    crm_workflow = [
        {"action": "Fetch_CRM_Leads", "criticality": ActionCriticality.READ_ONLY, "func": tool_fetch_crm_leads},
        {"action": "Qualify_Lead_Scores", "criticality": ActionCriticality.COMPUTATIONAL, "func": tool_qualify_leads},
        {"action": "Dispatch_Outreach_Emails", "criticality": ActionCriticality.MUTATIVE_CRITICAL, "func": tool_dispatch_crm_emails}
    ]

    worker1 = OperationalWorkerPoC("EXEC-CRM-2026", "Business_CRM_Operations", engine)
    
    # Run in async_mode=True to demonstrate non-blocking suspension
    status = worker1.execute_plan(crm_workflow, async_mode=True)

    if status == AgentState.PAUSED_AWAITING_SIGN_OFF:
        print("\n[INFO] Simulating external operator sign-off via asynchronous webhook/CLI...")
        time.sleep(0.5)
        worker1.resume_execution(decision="APPROVED", steps=crm_workflow)

    # --- Scenario 2: Code Security & Existence-Gap Audit ---
    audit_workflow = [
        {"action": "Scan_AST_Imports", "criticality": ActionCriticality.READ_ONLY, "func": tool_scan_ast_imports},
        {"action": "Verify_Existence_Gaps", "criticality": ActionCriticality.COMPUTATIONAL, "func": tool_verify_existence_gap},
        {"action": "Apply_Git_Patch", "criticality": ActionCriticality.MUTATIVE_CRITICAL, "func": tool_apply_git_patch}
    ]

    worker2 = OperationalWorkerPoC("EXEC-AUDIT-2026", "Codebase_Security_Audit", engine)
    worker2.execute_plan(audit_workflow, auto_approve=True)

    # --- Scenario 3: Audiovisual Synthesis (Remotion Pipeline) ---
    media_workflow = [
        {"action": "Parse_Remotion_Script", "criticality": ActionCriticality.READ_ONLY, "func": tool_parse_remotion_script},
        {"action": "Render_Preview_Frames", "criticality": ActionCriticality.COMPUTATIONAL, "func": tool_render_preview_frames},
        {"action": "Publish_4K_Master", "criticality": ActionCriticality.MUTATIVE_CRITICAL, "func": tool_publish_4k_master}
    ]

    worker3 = OperationalWorkerPoC("EXEC-MEDIA-2026", "Audiovisual_Remotion_Synthesis", engine)
    worker3.execute_plan(media_workflow, auto_approve=True)

    # --- Cryptographic Audit Ledger Verification ---
    integrity_valid = engine.verify_ledger_integrity()

    print("\n" + "═" * 80)
    print(f"   CRYPTOGRAPHIC AUDIT LEDGER (SCITT Tamper-Evident SHA-256 Chain)")
    print(f"   Ledger Verification Status: [{'VERIFIED OK' if integrity_valid else 'CORRUPTED'}]")
    print("═" * 80)

    cur = engine._conn.cursor()
    cur.execute("SELECT id, execution_id, action_name, decision, cryptographic_digest FROM audit_ledger ORDER BY id ASC")
    for r in cur.fetchall():
        print(f" Block #{r[0]} | Exec: {r[1]} | Action: {r[2]} | Decision: {r[3]} | Digest: {r[4][:12]}...{r[4][-12:]}")
    print("═" * 80)


if __name__ == "__main__":
    main()
