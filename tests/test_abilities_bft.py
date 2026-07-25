import pytest
from typing import Tuple
from babylon60.bft.lexicon import BFTLexicon
from babylon60.bft.abilities import BFTAbilityHandler, AbilityViolation

@pytest.fixture
def bft_env() -> Tuple[BFTLexicon, BFTAbilityHandler]:
    lex = BFTLexicon()
    handler = BFTAbilityHandler(lex)
    return lex, handler

@pytest.mark.asyncio
async def test_ability_isolation_context(bft_env: Tuple[BFTLexicon, BFTAbilityHandler]) -> None:
    lex, handler = bft_env
    
    async def mock_io_write(data: str) -> bool:
        return True
        
    io_hash = handler.hash_io
    handler.register_handler(io_hash, mock_io_write)
    
    # Baseline: no abilities claimed (Should Fail-Fast)
    with pytest.raises(AbilityViolation):
        await handler.execute(io_hash, "malicious_data")
        
    # Claim the ability in the current context
    with handler.abilities_scope(frozenset([io_hash])):
        # Execution succeeds implicitly inside the context
        res = await handler.execute(io_hash, "authorized_data")
        assert res is True
        
    # Out of context: Should Fail-Fast again
    with pytest.raises(AbilityViolation):
        await handler.execute(io_hash, "malicious_data_2")
