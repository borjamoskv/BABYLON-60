# Auto-generated entropy profiler for KIMI k3 layers (C5-REAL Physical Simulation)
import json
from typing import Any
import math
import hashlib


def softmax(logits: list[float], temperature: float) -> list[float]:
    # Stabilize logits by subtracting the max value
    max_logit = max(logits)
    scaled = [(logit - max_logit) / temperature for logit in logits]
    exp_scaled = [math.exp(s) for s in scaled]
    sum_exp = sum(exp_scaled)
    return [e / sum_exp for e in exp_scaled]


def calculate_shannon_entropy(probs: list[float]) -> float:
    entropy = 0.0
    for p in probs:
        if p > 0.0:
            entropy -= p * math.log(p)
    return entropy


def main() -> None:
    # Simulated logit distribution from a typical layer 24 vocabulary projection (size N=100)
    # Introducing a peak of corporate alignment (censorship token at index 0) and creative tails
    logits = [10.0 if i == 0 else (5.0 if i % 10 == 0 else 1.0) for i in range(100)]

    temperatures = [t * 0.1 for t in range(1, 21)]  # From 0.1 to 2.0
    s_max = math.log(len(logits))

    profile: dict[str, Any] = {
        "metadata": {
            "model_target": "KIMI-k3-Residual-Stream",
            "layer_source": 24,
            "dimension": len(logits),
            "max_possible_entropy": s_max,
        },
        "datapoints": [],
    }

    for t in temperatures:
        probs = softmax(logits, t)
        entropy = calculate_shannon_entropy(probs)
        exergy = s_max - entropy
        profile["datapoints"].append(
            {
                "temperature": round(t, 2),
                "shannon_entropy": entropy,
                "exergy_reduction": exergy,
                "top_token_probability": probs[0],
            }
        )

    output_path = "cortex/artifacts/reports/kimi_entropy_profile.json"
    with open(output_path, "w") as f:
        json.dump(profile, f, indent=2)

    # Calculate Blake3/SHA3-256 equivalent hash of target content
    json_bytes = json.dumps(profile, sort_keys=True).encode("utf-8")
    profile_hash = hashlib.sha3_256(json_bytes).hexdigest()

    print(f"CRYSTALLIZED_JSON_HASH: {profile_hash}")


if __name__ == "__main__":
    main()
