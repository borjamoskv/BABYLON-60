"""
CAM-5.0 Abstract Effect Observation Machine Core Engine.
Implements single step transition: step(S, Program) -> (S', ObservedEffects)
"""

from cortex.aem.effects import AlgebraicEffect, CapabilitySet, EffectProgram
from cortex.aem.isa import (
    CapabilityError,
    Handle,
    InstructionFamily,
    IntegrityError,
)
from cortex.aem.space import ObjectSpace


class AbstractEffectMachine:
    def __init__(self) -> None:
        self.space = ObjectSpace()
        self.capabilities: dict[str, CapabilitySet] = {}
        self.loaded_extensions: set[str] = set()

    def grant_agent_capabilities(
        self, agent_id: str, allowed_families: set[InstructionFamily]
    ) -> None:
        self.capabilities[agent_id] = CapabilitySet(allowed_families=allowed_families)

    def step(
        self, agent_id: str, program: EffectProgram
    ) -> tuple[ObjectSpace, list[AlgebraicEffect]]:
        observed_effects: list[AlgebraicEffect] = []
        caps = self.capabilities.get(agent_id)

        for family, params in program.operations:
            effect = AlgebraicEffect(family=family)
            if not caps or not caps.is_authorized(effect):
                raise CapabilityError(
                    f"Capability Denied: Agent '{agent_id}' lacks instruction family {family.value}"
                )

            if family == InstructionFamily.WRITE:
                op_type = params.get("op", "ALLOC")
                if op_type == "ALLOC":
                    payload = params.get("payload")
                    allocated_handle = self.space.allocate(payload)
                    params["result_handle"] = allocated_handle
                elif op_type == "MUTATE":
                    target_h = params.get("handle")
                    if isinstance(target_h, Handle):
                        self.space.lookup(target_h)
                        self.space.objects[target_h] = params.get("payload")
                elif op_type == "RELEASE":
                    target_h = params.get("handle")
                    if isinstance(target_h, Handle):
                        self.space.release(target_h)

            elif family == InstructionFamily.READ:
                target_h = params.get("handle")
                if isinstance(target_h, Handle):
                    params["result_val"] = self.space.lookup(target_h)

            elif family == InstructionFamily.CONTROL:
                op_type = params.get("op", "ASSERT")
                if op_type == "ASSERT":
                    if not params.get("predicate", True):
                        raise IntegrityError("ASSERT Predicate evaluation failed: False")
                elif op_type == "LOAD_EXTENSION":
                    ext_uri = str(params.get("uri", ""))
                    self.loaded_extensions.add(ext_uri)

            observed_effects.append(effect)

        return self.space, observed_effects
