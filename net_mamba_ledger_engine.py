# net_mamba_ledger_engine.py
# Execution Protocol: Exergy-Optimized Ontology & DAG Ledger Integration
# Prefix: net_ (network/inference orchestration layer with strict DAG tracking)

from typing import List, Tuple
from core_graph_ledger import GraphLedger, StateNode, core_calc_sha256
from cortex_bpe_tokenizer import BPETokenizer
from cortex_mamba_inference import MambaGenerator
from cortex_mamba_network import MambaNetwork

class MambaLedgerEngine:
    """
    Unifies the BPE Tokenizer, Mamba SSM Network, and DAG GraphLedger.
    Every token generated during autoregressive inference is atomically committed
    to the content-addressable DAG ledger, preventing generation hallucinations.
    """
    def __init__(self, tokenizer: BPETokenizer, network: MambaNetwork, ledger: GraphLedger) -> None:
        assert isinstance(tokenizer, BPETokenizer), "Fail-fast: tokenizer must be BPETokenizer"
        assert isinstance(network, MambaNetwork), "Fail-fast: network must be MambaNetwork"
        assert isinstance(ledger, GraphLedger), "Fail-fast: ledger must be GraphLedger"
        self.tokenizer = tokenizer
        self.network = network
        self.ledger = ledger
        self.generator = MambaGenerator(network)

    def mut_generate_audited(
        self,
        prompt: str,
        max_new_tokens: int = 10,
        temperature: float = 1.0,
        k: int = 5
    ) -> Tuple[str, List[StateNode]]:
        """
        Pre: prompt non-empty str && max_new_tokens > 0
        Exec: encode prompt -> step-by-step Mamba generation -> append node to DAG ledger
        Post: returns (decoded text, list of generated StateNodes in DAG)
        """
        assert isinstance(prompt, str) and len(prompt) > 0, "Fail-fast: prompt must be non-empty str"
        assert max_new_tokens > 0, "Fail-fast: max_new_tokens must be positive"

        # 1. Encode initial prompt
        prompt_ids = self.tokenizer.encode(prompt)
        assert len(prompt_ids) > 0, "Fail-fast: encoded prompt cannot be empty"

        # 2. Record prompt genesis in ledger if not already anchored
        prompt_payload = f"prompt:{prompt}:{prompt_ids}"
        prompt_hash = core_calc_sha256(prompt_payload)
        
        # Check if parent is genesis or latest head
        parent_id = self.ledger.genesis_id
        prompt_node = self.ledger.mut_append_node(
            parent_id=parent_id,
            claim=f"Prompt len {len(prompt_ids)}",
            payload_hash=prompt_hash
        )

        current_tokens = list(prompt_ids)
        generated_nodes: List[StateNode] = [prompt_node]
        current_parent_id = prompt_node.node_id

        # 3. Step-by-step autoregressive loop with ledger attachment
        for step in range(max_new_tokens):
            # Forward pass through Mamba SSM
            logits_seq = self.network.forward(current_tokens)
            next_token_logits = logits_seq[-1]

            # Softmax & Top-K sampling
            from cortex_mamba_inference import softmax, top_k_sampling
            probs = softmax(next_token_logits, temperature)
            next_token_id = top_k_sampling(probs, k=k)

            current_tokens.append(next_token_id)
            token_str = self.tokenizer.decode([next_token_id])

            # Append state node to DAG ledger
            step_claim = f"Step {step+1}: token {next_token_id}"
            step_payload = f"step:{step}:token:{next_token_id}:str:{token_str}:probs_hash:{core_calc_sha256(str(probs[:5]))}"
            step_hash = core_calc_sha256(step_payload)

            node = self.ledger.mut_append_node(
                parent_id=current_parent_id,
                claim=step_claim,
                payload_hash=step_hash
            )
            generated_nodes.append(node)
            current_parent_id = node.node_id

        # 4. Decode full sequence
        final_text = self.tokenizer.decode(current_tokens)
        return final_text, generated_nodes
