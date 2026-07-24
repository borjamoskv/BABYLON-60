from core_graph_ledger import GraphLedger
from cortex_bpe_tokenizer import BPETokenizer
from cortex_mamba_network import MambaNetwork
from net_mamba_ledger_engine import MambaLedgerEngine


def test_audited_generation_flow() -> None:
    """Verifica que cada token generado por el modelo Mamba sea insertado en el DAG Ledger."""
    tokenizer = BPETokenizer()
    tokenizer.train("hello world mamba exergy compute", num_merges=10)

    network = MambaNetwork(vocab_size=300, d_model=16, d_state=4, n_layers=2)
    ledger = GraphLedger()

    engine = MambaLedgerEngine(tokenizer=tokenizer, network=network, ledger=ledger)

    prompt = "hello"
    final_text, cert = engine.mut_generate_audited(prompt=prompt, max_new_tokens=5, temperature=0.5)

    assert isinstance(final_text, str)
    assert len(final_text) > len(prompt)
    assert cert.verify() is True
    assert cert.residual_microbits >= 0

    assert len(ledger.crdt.state) == 6


def test_mamba_ledger_fail_fast():
    import pytest

    tokenizer = BPETokenizer()
    network = MambaNetwork(vocab_size=300, d_model=16, d_state=4, n_layers=2)
    ledger = GraphLedger()
    engine = MambaLedgerEngine(tokenizer=tokenizer, network=network, ledger=ledger)

    with pytest.raises(AssertionError, match="Fail-fast: prompt must be non-empty str"):
        engine.mut_generate_audited(prompt="", max_new_tokens=5)

    with pytest.raises(AssertionError, match="Fail-fast: max_new_tokens must be positive"):
        engine.mut_generate_audited(prompt="hello", max_new_tokens=0)
