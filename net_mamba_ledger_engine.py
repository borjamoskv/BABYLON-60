from core_graph_ledger import GraphLedger, StateNode
from cortex_bpe_tokenizer import BPETokenizer
from cortex_mamba_inference import MambaGenerator
from cortex_mamba_network import MambaNetwork
from proof_kernel.canonicalizer import hash_evidence
from proof_kernel.certificates import ClosureCertificate


class MambaLedgerEngine:
    def __init__(self, tokenizer: BPETokenizer, network: MambaNetwork, ledger: GraphLedger) -> None:
        assert isinstance(tokenizer, BPETokenizer), "Fail-fast: tokenizer must be BPETokenizer"
        assert isinstance(network, MambaNetwork), "Fail-fast: network must be MambaNetwork"
        assert isinstance(ledger, GraphLedger), "Fail-fast: ledger must be GraphLedger"
        self.tokenizer = tokenizer
        self.network = network
        self.ledger = ledger
        self.generator = MambaGenerator(network)

    def mut_generate_audited(
        self, prompt: str, max_new_tokens: int = 10, temperature: float = 1.0, k: int = 5
    ) -> tuple[str, ClosureCertificate]:
        assert isinstance(prompt, str) and len(prompt) > 0, "Fail-fast: prompt must be non-empty str"
        assert max_new_tokens > 0, "Fail-fast: max_new_tokens must be positive"
        prompt_ids = self.tokenizer.encode(prompt)
        assert len(prompt_ids) > 0, "Fail-fast: encoded prompt cannot be empty"
        prompt_payload = {"type": "prompt", "text": prompt, "ids": prompt_ids}
        prompt_hash = hash_evidence(prompt_payload)
        parent_id = self.ledger.genesis_id
        prompt_node = self.ledger.mut_append_node(
            parent_id=parent_id, claim=f"Prompt len {len(prompt_ids)}", payload_hash=prompt_hash
        )
        current_tokens = list(prompt_ids)
        generated_nodes: list[StateNode] = [prompt_node]
        current_parent_id = prompt_node.node_id
        for step in range(max_new_tokens):
            logits_seq = self.network.forward(current_tokens)
            next_token_logits = logits_seq[-1]
            from cortex_mamba_inference import softmax, top_k_sampling

            probs = softmax(next_token_logits, temperature)
            next_token_id = top_k_sampling(probs, k=k)
            current_tokens.append(next_token_id)
            token_str = self.tokenizer.decode([next_token_id])
            step_claim = f"Step {step + 1}: token {next_token_id}"
            micro_probs = [int(float(p) * 1000000) for p in probs[:5]]
            step_payload = {
                "step": step,
                "token": next_token_id,
                "str": token_str,
                "probs_hash": hash_evidence(micro_probs),
            }
            step_hash = hash_evidence(step_payload)
            node = self.ledger.mut_append_node(parent_id=current_parent_id, claim=step_claim, payload_hash=step_hash)
            generated_nodes.append(node)
            current_parent_id = node.node_id
        final_text = self.tokenizer.decode(current_tokens)
        crdt_entropy = self.ledger.crdt.measure_entropy()
        cert = ClosureCertificate(
            evidence_hash=prompt_hash,
            ruleset_hash=hash_evidence({"model": "mamba", "temperature_milli": int(temperature * 1000), "k": k}),
            final_state=self.ledger.crdt.to_dict(),
            residual_microbits=crdt_entropy,
            epsilon_threshold=1000000,
        )
        cert.verify()
        return (final_text, cert)
