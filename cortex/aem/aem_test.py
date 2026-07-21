"""
Unit test suite for CAM-3.0 Abstract Effect Machine (AEM).
"""

import pytest
from cortex.aem.effects import EffectCategory
from cortex.aem.isa import CapabilityError, IntegrityError, InstructionType
from cortex.aem.machine import AbstractEffectMachine


def test_aem_object_space_alloc_load_bind() -> None:
    machine = AbstractEffectMachine()
    machine.grant_agent_capabilities(
        "agent_01",
        {
            EffectCategory.READ_STORE,
            EffectCategory.WRITE_STORE,
            EffectCategory.APPEND_LEDGER,
        },
    )

    # Alloc payloads
    h1 = machine.execute(
        agent_id="agent_01",
        instruction=InstructionType.ALLOC,
        payload={"claim": "System is stable"},
    )
    h2 = machine.execute(
        agent_id="agent_01",
        instruction=InstructionType.ALLOC,
        payload={"evidence": "All 366 unit tests passed"},
    )

    assert h1 != h2

    # Load payloads
    val1 = machine.execute(
        agent_id="agent_01", instruction=InstructionType.LOAD, handle_a=h1
    )
    assert val1 == {"claim": "System is stable"}

    # Bind handles
    machine.execute(
        agent_id="agent_01",
        instruction=InstructionType.LINK,
        handle_a=h2,
        handle_b=h1,
        relation_tag="supports",
    )

    assert machine.space.bindings[(h2, h1)] == "supports"


def test_aem_capability_error_enforcement() -> None:
    machine = AbstractEffectMachine()
    # Agent only has READ capability
    machine.grant_agent_capabilities("agent_read_only", {EffectCategory.READ_STORE})

    # Alloc requires WRITE_STORE -> CapabilityError expected
    with pytest.raises(CapabilityError, match="lacks effect Write\\(Store\\)"):
        machine.execute(
            agent_id="agent_read_only",
            instruction=InstructionType.ALLOC,
            payload={"data": "write_attempt"},
        )


def test_aem_assert_and_commit() -> None:
    machine = AbstractEffectMachine()
    machine.grant_agent_capabilities(
        "agent_full",
        {
            EffectCategory.READ_STORE,
            EffectCategory.WRITE_STORE,
            EffectCategory.APPEND_LEDGER,
        },
    )

    # Valid ASSERT
    assert machine.execute(
        agent_id="agent_full", instruction=InstructionType.ASSERT, predicate=True
    ) is True

    # Failed ASSERT -> IntegrityError expected
    with pytest.raises(IntegrityError, match="ASSERT Predicate evaluation failed"):
        machine.execute(
            agent_id="agent_full", instruction=InstructionType.ASSERT, predicate=False
        )

    # Commit event log
    entry_hash = machine.execute(
        agent_id="agent_full", instruction=InstructionType.COMMIT
    )
    assert isinstance(entry_hash, str)
    assert len(entry_hash) == 64
    assert len(machine.event_ledger) == 1
