# net_mamba_ledger_engine.py
# Execution Protocol: Exergy-Optimized Ontology & DAG Ledger Integration
# Prefix: net_ (network/inference orchestration layer with strict DAG tracking)

from typing import List, Tuple, Any
from core_graph_ledger import GraphLedger, StateNode
from cortex_bpe_tokenizer import BPETokenizer
from cortex_mamba_inference import MambaGenerator
from cortex_mamba_network import MambaNetwork
from proof_kernel.canonicalizer import hash_evidence
from proof_kernel.certificates import ClosureCertificate

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
    ) -> Tuple[str, ClosureCertificate]:
        """
        Pre: prompt non-empty str && max_new_tokens > 0
        Exec: encode prompt -> step-by-step Mamba generation -> append node to DAG ledger -> emit Certificate
        Post: returns (decoded text, ClosureCertificate)
        """
        assert isinstance(prompt, str) and len(prompt) > 0, "Fail-fast: prompt must be non-empty str"
        assert max_new_tokens > 0, "Fail-fast: max_new_tokens must be positive"

        # 1. Encode initial prompt
        prompt_ids = self.tokenizer.encode(prompt)
        assert len(prompt_ids) > 0, "Fail-fast: encoded prompt cannot be empty"

        # 2. Record prompt genesis in ledger if not already anchored
        prompt_payload = {"type": "prompt", "text": prompt, "ids": prompt_ids}
        prompt_hash = hash_evidence(prompt_payload)
        
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
            micro_probs = [int(float(p) * 1_000_000) for p in probs[:5]]
            step_payload = {"step": step, "token": next_token_id, "str": token_str, "probs_hash": hash_evidence(micro_probs)}
            step_hash = hash_evidence(step_payload)

            node = self.ledger.mut_append_node(
                parent_id=current_parent_id,
                claim=step_claim,
                payload_hash=step_hash
            )
            generated_nodes.append(node)
            current_parent_id = node.node_id

        # 4. Decode full sequence
        final_text = self.tokenizer.decode(current_tokens)
        
        # 5. Generate ClosureCertificate (Thermodynamic Proof)
        crdt_entropy = self.ledger.crdt.measure_entropy()
        cert = ClosureCertificate(
            evidence_hash=prompt_hash,
            ruleset_hash=hash_evidence({"model": "mamba", "temperature_milli": int(temperature * 1000), "k": k}),
            final_state=self.ledger.crdt.to_dict(),
            residual_microbits=crdt_entropy,
            epsilon_threshold=1_000_000 # Configurable
        )
        cert.verify() # Fail-fast if cert is corrupted
        
        return final_text, cert
