# C5-REAL EXERGY CERTIFIED
"""
Unit test suite for CAM-5.0 Abstract Effect Observation Machine Core.
"""

import pytest
from cortex.aem.effects import EffectProgram
from cortex.aem.isa import CapabilityError, ExecutionError, Handle, InstructionFamily, IntegrityError
from cortex.aem.machine import AbstractEffectMachine


def test_cam5_step_function_and_families() -> None:
    machine = AbstractEffectMachine()
    machine.grant_agent_capabilities(
        "agent_01",
        {InstructionFamily.READ, InstructionFamily.WRITE, InstructionFamily.CONTROL},
    )

    alloc_params = {"op": "ALLOC", "payload": "Minimal State Object"}
    prog = EffectProgram(operations=[(InstructionFamily.WRITE, alloc_params)])

    space, effects = machine.step("agent_01", prog)
    assert len(effects) == 1
    assert effects[0].family == InstructionFamily.WRITE
    h = alloc_params["result_handle"]
    assert isinstance(h, Handle)

    # Read back payload
    read_params = {"handle": h}
    prog_read = EffectProgram(operations=[(InstructionFamily.READ, read_params)])
    _, read_effects = machine.step("agent_01", prog_read)
    assert len(read_effects) == 1
    assert read_params["result_val"] == "Minimal State Object"


def test_cam5_capability_denial() -> None:
    machine = AbstractEffectMachine()
    # Read-only agent
    machine.grant_agent_capabilities("agent_read", {InstructionFamily.READ})

    prog_write = EffectProgram(
        operations=[(InstructionFamily.WRITE, {"op": "ALLOC", "payload": "fail"})]
    )

    with pytest.raises(CapabilityError, match="lacks instruction family WRITE"):
        machine.step("agent_read", prog_write)


def test_cam5_control_assert_and_extension() -> None:
    machine = AbstractEffectMachine()
    machine.grant_agent_capabilities("agent_ctrl", {InstructionFamily.CONTROL})

    # Failed ASSERT
    prog_fail_assert = EffectProgram(
        operations=[(InstructionFamily.CONTROL, {"op": "ASSERT", "predicate": False})]
    )
    with pytest.raises(IntegrityError, match="ASSERT Predicate evaluation failed"):
        machine.step("agent_ctrl", prog_fail_assert)

    # Load extension
    prog_ext = EffectProgram(
        operations=[(InstructionFamily.CONTROL, {"op": "LOAD_EXTENSION", "uri": "cesl://ledger"})]
    )
    _, effects = machine.step("agent_ctrl", prog_ext)
    assert len(effects) == 1
    assert "cesl://ledger" in machine.loaded_extensions


def test_cam5_mutate_and_release_ops() -> None:
    machine = AbstractEffectMachine()
    machine.grant_agent_capabilities("agent_rw", {InstructionFamily.READ, InstructionFamily.WRITE})

    # Alloc
    alloc_p = {"op": "ALLOC", "payload": "Initial Value"}
    machine.step("agent_rw", EffectProgram(operations=[(InstructionFamily.WRITE, alloc_p)]))
    h = alloc_p["result_handle"]
    assert isinstance(h, Handle)

    # Mutate
    mutate_p = {"op": "MUTATE", "handle": h, "payload": "Mutated Value"}
    machine.step("agent_rw", EffectProgram(operations=[(InstructionFamily.WRITE, mutate_p)]))

    read_p = {"handle": h}
    machine.step("agent_rw", EffectProgram(operations=[(InstructionFamily.READ, read_p)]))
    assert read_p["result_val"] == "Mutated Value"

    # Release
    release_p = {"op": "RELEASE", "handle": h}
    machine.step("agent_rw", EffectProgram(operations=[(InstructionFamily.WRITE, release_p)]))

    with pytest.raises(ExecutionError, match="Invalid Handle"):
        read_p2 = {"handle": h}
        machine.step("agent_rw", EffectProgram(operations=[(InstructionFamily.READ, read_p2)]))

