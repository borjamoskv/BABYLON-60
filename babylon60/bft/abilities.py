"""
C5-REAL Algebraic Effects (Abilities) Interceptor.
Mimics Unison's capability isolation inside Python via BFT Lexicon Hashes.
"""
import asyncio
import inspect
from typing import Any, Callable, Dict, TypeVar, List
from babylon60.bft.lexicon import BFTLexicon

T = TypeVar('T')

class AbilityViolation(Exception):
    """Raised when a function attempts an effect without claiming the Ability."""
    pass

class BFTAbilityHandler:
    def __init__(self, lexicon: BFTLexicon) -> None:
        self.lexicon = lexicon
        # Load capability hashes
        self.hash_io = lexicon.get_concept_hash("TYPE::Ability::IO")
        self.hash_state = lexicon.get_concept_hash("TYPE::Ability::State")
        self.hash_exception = lexicon.get_concept_hash("TYPE::Ability::Exception")
        
        self.handlers: Dict[str, Callable[..., Any]] = {}

    def register_handler(self, ability_hash: str, handler_fn: Callable[..., Any]) -> None:
        """Injects the physical execution layer for a specific ability."""
        self.handlers[ability_hash] = handler_fn

    async def execute_with_abilities(self, 
                                     claimed_abilities: List[str], 
                                     effect_hash: str, 
                                     *args: Any, **kwargs: Any) -> Any:
        """
        Executes a side-effect if and only if the caller explicitly claimed the ability.
        """
        if effect_hash not in claimed_abilities:
            effect_name = self.lexicon.resolve_hash(effect_hash) or effect_hash
            raise AbilityViolation(f"C5-REAL: Execution halted. Missing Ability: {effect_name}")
            
        if effect_hash not in self.handlers:
            effect_name = self.lexicon.resolve_hash(effect_hash) or effect_hash
            raise NotImplementedError(f"C5-REAL: No physical handler registered for {effect_name}")
            
        handler = self.handlers[effect_hash]
        if inspect.iscoroutinefunction(handler):
            return await handler(*args, **kwargs)
        return handler(*args, **kwargs)
