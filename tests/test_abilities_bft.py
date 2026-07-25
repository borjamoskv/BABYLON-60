import pytest

from babylon60.bft.abilities import AbilityViolation, BFTAbilityHandler
from babylon60.bft.lexicon import BFTLexicon


@pytest.fixture
def bft_env() -> tuple[BFTLexicon, BFTAbilityHandler]:
    lex = BFTLexicon()
    handler = BFTAbilityHandler(lex)
    return (lex, handler)


@pytest.mark.asyncio
async def test_ability_isolation_context(bft_env: tuple[BFTLexicon, BFTAbilityHandler]) -> None:
    lex, handler = bft_env

    async def mock_io_write(data: str) -> bool:
        return True

    io_hash = handler.hash_io
    handler.register_handler(io_hash, mock_io_write)
    with pytest.raises(AbilityViolation):
        await handler.execute(io_hash, "malicious_data")
    with handler.abilities_scope(frozenset([io_hash])):
        res = await handler.execute(io_hash, "authorized_data")
        assert res is True
    with pytest.raises(AbilityViolation):
        await handler.execute(io_hash, "malicious_data_2")
