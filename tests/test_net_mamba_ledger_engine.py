# test_net_mamba_ledger_engine.py
# Prefix: test_ (empirical unit falsification for the audited engine)

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
    final_text, nodes = engine.mut_generate_audited(prompt=prompt, max_new_tokens=5, temperature=0.5)
    
    # Assert nodes count: 1 prompt node + 5 generated tokens = 6 nodes
    assert len(nodes) == 6
    assert nodes[0].claim_summary.startswith("Prompt len")
    assert nodes[-1].claim_summary.startswith("Step 5:")
    
    # Verify that the DAG path is continuous and trace-able from head back to genesis
    path = ledger.core_get_path(nodes[-1].node_id)
    assert len(path) == 6
    for i in range(len(nodes)):
        assert path[i].node_id == nodes[i].node_id

def test_engine_fail_fast_on_invalid_prompt() -> None:
    """Verifica que el motor rechace inputs vacíos inmediatamente sin quemar ciclos en la red neuronal."""
    tokenizer = BPETokenizer()
    network = MambaNetwork(vocab_size=300, d_model=16, d_state=4, n_layers=2)
    ledger = GraphLedger()
    engine = MambaLedgerEngine(tokenizer=tokenizer, network=network, ledger=ledger)
    
    import pytest
    with pytest.raises(AssertionError, match="prompt must be non-empty str"):
        engine.mut_generate_audited(prompt="", max_new_tokens=5)
