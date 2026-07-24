import pytest
import asyncio
from typing import Tuple
from babylon60.bft.lexicon import BFTLexicon
from babylon60.bft.abilities import BFTAbilityHandler, AbilityViolation

@pytest.fixture
def bft_env() -> Tuple[BFTLexicon, BFTAbilityHandler]:
    lex = BFTLexicon()
    handler = BFTAbilityHandler(lex)
    return lex, handler

@pytest.mark.asyncio
async def test_ability_isolation(bft_env: Tuple[BFTLexicon, BFTAbilityHandler]) -> None:
    lex, handler = bft_env
    
    # Mock an IO operation (e.g. write to disk)
    async def mock_io_write(data: str) -> bool:
        return True
        
    io_hash = handler.hash_io
    handler.register_handler(io_hash, mock_io_write)
    
    # Try to execute IO without claiming the ability (Should Fail-Fast)
    with pytest.raises(AbilityViolation):
        await handler.execute_with_abilities([], io_hash, "malicious_data")
        
    # Execute IO while explicitly claiming the ability (Should Succeed)
    res = await handler.execute_with_abilities([io_hash], io_hash, "authorized_data")
    assert res is True
