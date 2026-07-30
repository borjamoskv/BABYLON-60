# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import pytest
import os
from datetime import datetime, timezone

from babylon60.engine import CortexEngine as AsyncCortexEngine
from babylon60.swarm.legion import AsyncSignalBus, SwarmSignal
from babylon60.swarm.generator_agent import GeneratorAgent
from babylon60.swarm.generator_squadron import GeneratorSquadron
from babylon60.crypto.keys import KeyManager, Verifier
from babylon60.crypto.hash_registry import cortex_hash
from babylon60.guards.landauer_guard import LandauerGuard


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_cortex.db"
    return str(db_file)


@pytest.mark.asyncio
async def test_generator_agent_execution(temp_db):
    """Verifies that GeneratorAgent generates, verifies entropy, and signs proposed ASTs."""
    km = KeyManager(service_name="test_generator_agent_crypto")
    bus = AsyncSignalBus()

    agent_id = "agent_gen_001"
    km.revoke_key(agent_id)

    # Initialize agent
    agent = GeneratorAgent(agent_id=agent_id, bus=bus, km=km)

    # Key pair should be automatically generated
    pub_key_b64 = km.get_public_key_b64(agent_id)
    assert pub_key_b64 is not None

    # Execute target spec
    signal = await agent.execute("spec_auth_v2")
    assert signal.status == "SUCCESS"
    assert signal.agent_id == agent_id

    # Verify signal payload contents
    payload = signal.payload
    assert payload["agent_id"] == agent_id
    assert "ast_code" in payload
    assert "signature_b64" in payload
    assert "timestamp" in payload

    # Verify Landauer entropy constraint (MIN_ENTROPY is 3.5)
    assert payload["entropy"] >= LandauerGuard.MIN_ENTROPY

    # Verify cryptographic signature
    p_hash = cortex_hash(payload["ast_code"].encode("utf-8"))
    sig_valid = Verifier.verify_signature(
        pub_key_b64, p_hash, payload["timestamp"], payload["signature_b64"]
    )
    assert sig_valid is True


@pytest.mark.asyncio
async def test_generator_squadron_crystallization(temp_db):
    """Verifies that GeneratorSquadron aggregates, executes BFT consensus, and logs to the Ledger."""
    # Initialize real CortexEngine with temp db
    engine = AsyncCortexEngine(temp_db)
    await engine.init_db()

    # Initialize squadron
    squadron = GeneratorSquadron(engine=engine)

    # Setup 3 replicas
    agent_ids = ["agent_1", "agent_2", "agent_3"]
    signals = []

    # Generate identical proposals for consensus
    ast_code = (
        "# [C5-REAL] Consensual AST Mutation CORTEX-TAINT\n"
        "def resolve(ctx):\n"
        "    ctx['resolved'] = True\n"
        "    return ctx\n"
    )

    for aid in agent_ids:
        agent = squadron._create_agent(aid)
        agent.simulated_code = ast_code
        sig = await agent.execute("mutate_resolver")
        signals.append(sig)

    # Run crystallization manually
    report = await squadron._crystallize(signals)

    # Assert consensus achieved
    assert report["consensus"] == "PASSED"
    assert report["winner"] in agent_ids
    assert ast_code in report["ast_code"]

    # Verify that the event was recorded in the database
    from babylon60.audit.ledger import EnterpriseAuditLedger
    from babylon60.database.core import connect_async_ctx

    async with connect_async_ctx(temp_db) as conn:
        ledger = EnterpriseAuditLedger(conn)
        await ledger.ensure_table()

        # Let's inspect the security audit log
        async with conn.execute(
            "SELECT action, actor_id, resource, status FROM security_audit_log ORDER BY id DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            assert row is not None
            action, actor_id, resource, status = row
            assert action == "QUORUM_CONSENSUS"
            assert actor_id == f"Squadron-{squadron.SQUAD_NAME}"
            assert resource == "ast_code"
            assert status == "SUCCESS"

    await engine.close()
