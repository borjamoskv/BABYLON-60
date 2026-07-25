import asyncio
import inspect
import contextlib
import contextvars
import typing
from contextvars import ContextVar
from typing import Any, Callable, Dict, TypeVar, FrozenSet
from babylon60.bft.lexicon import BFTLexicon
T = TypeVar('T')

class AbilityViolation(Exception):
    pass
_claimed_abilities: ContextVar[FrozenSet[str]] = ContextVar('_claimed_abilities', default=frozenset())

class BFTAbilityHandler:

    def __init__(self, lexicon: BFTLexicon) -> None:
        self.lexicon = lexicon
        self.hash_io = lexicon.get_concept_hash('TYPE::Ability::IO')
        self.hash_state = lexicon.get_concept_hash('TYPE::Ability::State')
        self.hash_exception = lexicon.get_concept_hash('TYPE::Ability::Exception')
        self.handlers: Dict[str, Callable[..., Any]] = {}

    def register_handler(self, ability_hash: str, handler_fn: Callable[..., Any]) -> None:
        self.handlers[ability_hash] = handler_fn

    def claim_abilities(self, abilities: FrozenSet[str]) -> contextvars.Token[FrozenSet[str]]:
        return _claimed_abilities.set(abilities)

    def release_abilities(self, token: contextvars.Token[FrozenSet[str]]) -> None:
        _claimed_abilities.reset(token)

    @contextlib.contextmanager
    def abilities_scope(self, abilities: FrozenSet[str]) -> typing.Iterator[None]:
        token = self.claim_abilities(abilities)
        try:
            yield
        finally:
            self.release_abilities(token)

    async def execute(self, effect_hash: str, *args: Any, **kwargs: Any) -> Any:
        active_claims = _claimed_abilities.get()
        if effect_hash not in active_claims:
            effect_name = self.lexicon.resolve_hash(effect_hash) or effect_hash
            raise AbilityViolation(f'C5-REAL: Execution halted. Missing Ability: {effect_name}')
        if effect_hash not in self.handlers:
            effect_name = self.lexicon.resolve_hash(effect_hash) or effect_hash
            raise NotImplementedError(f'C5-REAL: No physical handler registered for {effect_name}')
        handler = self.handlers[effect_hash]
        if inspect.iscoroutinefunction(handler):
            return await handler(*args, **kwargs)
        import functools
        func = functools.partial(handler, *args, **kwargs)
        return await asyncio.to_thread(func)