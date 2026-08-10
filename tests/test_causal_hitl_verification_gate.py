#!/usr/bin/env python3
"""
Unit tests for babylon60.extensions.swarm.verification_gate
Conforme a RULE[human_in_the_loop_causal_governance] y RULE[c5_real_invariants].
"""

import os
import pytest
from babylon60.extensions.swarm.verification_gate import (
    AgentState,
    CausalSignOffReceipt,
    RiskLevel,
    VerificationGate,
)


def test_verification_gate_risk_evaluation():
    gate = VerificationGate()

    # Read-only task -> LOW
    assert gate.evaluate_task({"action": "read_records"}) == RiskLevel.LOW

    # Build task -> MEDIUM
    assert gate.evaluate_task({"action": "run_build_test"}) == RiskLevel.MEDIUM

    # Patch task -> HIGH
    assert gate.evaluate_task({"action": "apply_code_patch"}) == RiskLevel.HIGH

    # Mutative / Deploy task -> CRITICAL
    assert gate.evaluate_task({"action": "deploy_production"}) == RiskLevel.CRITICAL
    assert gate.evaluate_task({"action": "read", "is_mutative": True}) == RiskLevel.CRITICAL


def test_verification_gate_critical_permission():
    gate = VerificationGate()
    exec_id = "EXEC-TEST-001"
    payload_critical = {"action": "deploy_production", "execution_id": exec_id}

    # Initially not allowed without sign-off receipt
    assert gate.is_allowed(payload_critical) is False

    # Register APPROVED sign-off receipt
    receipt = gate.register_sign_off(
        execution_id=exec_id,
        action_name="deploy_production",
        risk_level=RiskLevel.CRITICAL,
        decision="APPROVED"
    )

    assert isinstance(receipt, CausalSignOffReceipt)
    assert receipt.execution_id == exec_id
    assert receipt.decision == "APPROVED"
    assert len(receipt.cryptographic_digest) == 64

    # Now allowed under Causal Gate governance
    assert gate.is_allowed(payload_critical) is True


def test_verification_gate_cryptographic_ledger_integrity():
    gate = VerificationGate()

    for i in range(5):
        gate.register_sign_off(
            execution_id=f"EXEC-STEP-{i}",
            action_name=f"Action_{i}",
            risk_level=RiskLevel.HIGH if i % 2 == 0 else RiskLevel.CRITICAL,
            decision="APPROVED" if i != 2 else "REJECTED"
        )

    # Merkle hash chain must be verified
    assert gate.verify_ledger_integrity() is True


def test_verification_gate_snapshot_pause_resume():
    gate = VerificationGate()
    exec_id = "EXEC-SNAPSHOT-100"

    gate.save_snapshot(
        execution_id=exec_id,
        domain="Unit_Test_Domain",
        step=2,
        status=AgentState.PAUSED_AWAITING_SIGN_OFF,
        pending_action="commit_state",
        payload={"data": "test_payload"}
    )

    snapshot = gate.load_snapshot(exec_id)
    assert snapshot is not None
    assert snapshot["domain"] == "Unit_Test_Domain"
    assert snapshot["current_step"] == 2
    assert snapshot["status"] == AgentState.PAUSED_AWAITING_SIGN_OFF
    assert snapshot["pending_action"] == "commit_state"
    assert snapshot["payload"] == {"data": "test_payload"}
