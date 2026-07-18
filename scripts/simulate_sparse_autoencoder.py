# Auto-generated Sparse Autoencoder (SAE) simulator for KIMI k3 feature superposition (C5-REAL Simulation)
import json
import math
import hashlib

def relu(x):
    return max(0.0, x)

def l1_penalty(hidden_activations, l1_coeff):
    return sum(abs(h) for h in hidden_activations) * l1_coeff

def mse_loss(original, reconstructed):
    return sum((o - r) ** 2 for o, r in zip(original, reconstructed)) / len(original)

def main():
    # Activation vector from KIMI k3 Layer 24 (residual stream dimension Din=32)
    # Features in superposition: [0]=Semantic payload, [1]=Safety override activation
    original_activations = [0.1 * (i % 5) for i in range(32)]
    # Safety directive adds a massive bias to the first 4 dimensions
    aligned_activations = [
        o + 4.0 if i < 4 else o
        for i, o in enumerate(original_activations)
    ]
    
    # Simulating a dictionary (W_enc: 128 hidden neurons, 32 input dimensions)
    # Generates a pseudo-random sparse encoder weight matrix
    encoder_weights = [
        [math.sin(i * j) * 0.1 for j in range(32)]
        for i in range(128)
    ]
    encoder_bias = [-0.1 for _ in range(128)]
    
    # Decoder weights (tied or untied, here simple transpose representation for simulation)
    decoder_weights = [
        [math.sin(i * j) * 0.1 for i in range(128)]
        for j in range(32)
    ]
    
    sae_profile = {
        "metadata": {
            "target": "KIMI-k3-Residual-SAE",
            "dictionary_multiplier": 4, # 128 / 32
            "input_dim": 32,
            "hidden_dim": 128
        },
        "scenarios": {}
    }
    
    for label, activations in [("standard", original_activations), ("aligned_censored", aligned_activations)]:
        # Encode (forward pass to hidden space with bias and ReLU)
        hidden = []
        for h_idx in range(128):
            act_sum = sum(activations[i] * encoder_weights[h_idx][i] for i in range(32))
            hidden.append(relu(act_sum + encoder_bias[h_idx]))
            
        # Sparsity metrics
        l0_norm = sum(1 for h in hidden if h > 0.0)
        l1_norm = sum(hidden)
        
        # Decode (reconstruction back to Din=32)
        reconstructed = []
        for i in range(32):
            recon_sum = sum(hidden[h_idx] * decoder_weights[i][h_idx] for h_idx in range(128))
            reconstructed.append(recon_sum)
            
        mse = mse_loss(activations, reconstructed)
        
        sae_profile["scenarios"][label] = {
            "l0_sparsity_active_features": l0_norm,
            "l1_sparsity_norm": l1_norm,
            "reconstruction_mse": mse,
            "mean_hidden_activation": sum(hidden) / len(hidden)
        }
        
    output_path = "cortex/artifacts/reports/kimi_sae_reconstruction.json"
    with open(output_path, "w") as f:
        json.dump(sae_profile, f, indent=2)
        
    json_bytes = json.dumps(sae_profile, sort_keys=True).encode("utf-8")
    profile_hash = hashlib.sha3_256(json_bytes).hexdigest()
    
    print(f"CRYSTALLIZED_SAE_HASH: {profile_hash}")

if __name__ == "__main__":
    main()
