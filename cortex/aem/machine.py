"""
CAM-3.0 Abstract Effect Machine (AEM) Microkernel.
Executes micro-instructions over Object Space under algebraic effect capabilities.
"""

from dataclasses import dataclass, field
import hashlib
import time
from typing import Any

from cortex.aem.effects import AlgebraicEffect, CapabilitySet, EffectCategory
from cortex.aem.isa import (
    CapabilityError,
    Handle,
    InstructionType,
    IntegrityError,
)
from cortex.aem.space import ObjectSpace


@dataclass
class Event:
    instruction: InstructionType
    handle: Handle | None
    effect: AlgebraicEffect
    timestamp: float = field(default_factory=time.time)


class AbstractEffectMachine:
    def __init__(self) -> None:
        self.space = ObjectSpace()
        self.capabilities: dict[str, CapabilitySet] = {}
        self.event_ledger: list[dict[str, Any]] = []

    def grant_agent_capabilities(
        self, agent_id: str, allowed_effects: set[EffectCategory]
    ) -> None:
        self.capabilities[agent_id] = CapabilitySet(allowed_effects=allowed_effects)

    def execute(
        self,
        agent_id: str,
        instruction: InstructionType,
        payload: Any = None,
        handle_a: Handle | None = None,
        handle_b: Handle | None = None,
        relation_tag: str = "",
        predicate: bool = True,
    ) -> Handle | Any:
        # 1. Map Instruction to Required Algebraic Effect
        effect = self._map_instruction_to_effect(instruction)

        # 2. Enforce Capability Permissions
        caps = self.capabilities.get(agent_id)
        if not caps or not caps.is_authorized(effect):
            raise CapabilityError(
                f"Capability Denied: Agent '{agent_id}' lacks effect {effect.category.value}"
            )

        # 3. Micro-ISA Dispatcher
        if instruction == InstructionType.ALLOC:
            h = self.space.allocate(payload)
            self._log_event(instruction, h, effect)
            return h

        elif instruction == InstructionType.LOAD:
            if not handle_a:
                raise ValueError("LOAD requires handle_a")
            val = self.space.lookup(handle_a)
            self._log_event(instruction, handle_a, effect)
            return val

        elif instruction == InstructionType.STORE:
            if not handle_a:
                raise ValueError("STORE requires handle_a")
            self.space.lookup(handle_a)  # Verify exists
            self.space.objects[handle_a] = payload
            self._log_event(instruction, handle_a, effect)
            return handle_a

        elif instruction == InstructionType.LINK:
            if not handle_a or not handle_b:
                raise ValueError("LINK requires handle_a and handle_b")
            self.space.bind(handle_a, handle_b, relation_tag)
            self._log_event(instruction, handle_a, effect)
            return handle_a

        elif instruction == InstructionType.ASSERT:
            if not predicate:
                raise IntegrityError("ASSERT Predicate evaluation failed: False")
            self._log_event(instruction, None, effect)
            return True

        elif instruction == InstructionType.COMMIT:
            prev_hash = (
                self.event_ledger[-1]["entry_hash"]
                if self.event_ledger
                else "00000000000000000000000000000000"
            )
            raw = f"{prev_hash}:{time.time()}:{len(self.space.objects)}"
            entry_hash = hashlib.sha3_256(raw.encode("utf-8")).hexdigest()
            self.event_ledger.append(
                {"prev_hash": prev_hash, "entry_hash": entry_hash, "ts": time.time()}
            )
            self._log_event(instruction, None, effect)
            return entry_hash

        return None

    def _map_instruction_to_effect(
        self, instruction: InstructionType
    ) -> AlgebraicEffect:
        if instruction in (InstructionType.ALLOC, InstructionType.STORE, InstructionType.LINK, InstructionType.UNLINK):
            return AlgebraicEffect(category=EffectCategory.WRITE_STORE)
        elif instruction == InstructionType.LOAD:
            return AlgebraicEffect(category=EffectCategory.READ_STORE)
        elif instruction == InstructionType.COMMIT:
            return AlgebraicEffect(category=EffectCategory.APPEND_LEDGER)
        elif instruction == InstructionType.CALL:
            return AlgebraicEffect(category=EffectCategory.CALL_EXTERNAL)
        else:  # ASSERT, ABORT (Pure)
            return AlgebraicEffect(category=EffectCategory.READ_STORE)

    def _log_event(
        self, instruction: InstructionType, handle: Handle | None, effect: AlgebraicEffect
    ) -> None:
        Event(instruction=instruction, handle=handle, effect=effect)
