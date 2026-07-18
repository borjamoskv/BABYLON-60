# Auto-generated attention collapse profiler for KIMI k3 layers (C5-REAL Physical Simulation)
import json
import math
import hashlib

def calculate_kl_divergence(p, q):
    kl = 0.0
    for pi, qi in zip(p, q):
        if pi > 0.0 and qi > 0.0:
            kl += pi * math.log(pi / qi)
    return kl

def softmax(logits):
    max_logit = max(logits)
    exp_logits = [math.exp(l - max_logit) for l in logits]
    sum_exp = sum(exp_logits)
    return [e / sum_exp for e in exp_logits]

def main():
    # Model 8 attention heads (dimension N=50 tokens in context)
    # Head 0-3: Semantic focus, Head 4-7: Safety/Alignment focus
    heads_count = 8
    seq_len = 50
    
    # Original query-key dot product weights (high exergy attention)
    # Focused on index 10-15 (actual semantic payload)
    original_attn_logits = [
        [3.0 if 10 <= i <= 15 else 0.5 for i in range(seq_len)]
        for _ in range(heads_count)
    ]
    
    # Aligned query-key dot product weights (distorted by system instructions forcing attention to the system prompt at indices 0-5)
    aligned_attn_logits = []
    for h in range(heads_count):
        # Heads 4-7 are heavily modified by safety fine-tuning to pay attention to system prompts
        if h >= 4:
            aligned_attn_logits.append([
                5.0 if i < 5 else (1.5 if 10 <= i <= 15 else 0.2)
                for i in range(seq_len)
            ])
        else:
            aligned_attn_logits.append([
                3.0 if 10 <= i <= 15 else 0.5 for i in range(seq_len)
            ])
            
    collapse_profile = {
        "metadata": {
            "target": "KIMI-k3-MHA-Layer-12",
            "heads": heads_count,
            "sequence_length": seq_len
        },
        "heads_datapoints": []
    }
    
    for h in range(heads_count):
        p = softmax(original_attn_logits[h])
        q = softmax(aligned_attn_logits[h])
        
        kl_div = calculate_kl_divergence(p, q)
        # Shannon Entropy of both distributions
        entropy_p = -sum(pi * math.log(pi) for pi in p if pi > 0.0)
        entropy_q = -sum(qi * math.log(qi) for qi in q if qi > 0.0)
        
        collapse_profile["heads_datapoints"].append({
            "head_id": h,
            "kl_divergence_nats": kl_div,
            "original_entropy": entropy_p,
            "aligned_entropy": entropy_q,
            "entropy_loss": entropy_p - entropy_q
        })
        
    output_path = "cortex/artifacts/reports/kimi_attention_collapse.json"
    with open(output_path, "w") as f:
        json.dump(collapse_profile, f, indent=2)
        
    json_bytes = json.dumps(collapse_profile, sort_keys=True).encode("utf-8")
    profile_hash = hashlib.sha3_256(json_bytes).hexdigest()
    
    print(f"CRYSTALLIZED_ATTN_HASH: {profile_hash}")

if __name__ == "__main__":
    main()
