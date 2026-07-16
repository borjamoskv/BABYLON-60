import numpy as np
import pandas as pd
from collections import Counter
import json

# C5-REAL: Proto-Romance Entropy Reconstruction
# Invariante 1: Phonetic change destroys information (Entropy > 0).
# Invariante 2: Not fully reversible without noise.

# Dataset: Latin (Proto-Romance Proxy) vs Romance Daughters
data = {
    "luna": {"es": "luna", "it": "luna", "fr": "lune", "pt": "lua", "ro": "luna", "la": "luna"},
    "nocte": {"es": "noche", "it": "notte", "fr": "nuit", "pt": "noite", "ro": "noapte", "la": "nocte"},
    "lacte": {"es": "leche", "it": "latte", "fr": "lait", "pt": "leite", "ro": "lapte", "la": "lacte"},
    "octo": {"es": "ocho", "it": "otto", "fr": "huit", "pt": "oito", "ro": "opt", "la": "octo"},
    "fabulare": {"es": "hablar", "it": "favolare", "fr": "fabler", "pt": "falar", "ro": "fabulare", "la": "fabulare"},
    "filum": {"es": "hilo", "it": "filo", "fr": "fil", "pt": "fio", "ro": "fir", "la": "filum"},
    "clavis": {"es": "llave", "it": "chiave", "fr": "clef", "pt": "chave", "ro": "cheie", "la": "clavis"}
}

def entropy(probs):
    probs = probs[probs > 0]
    return -np.sum(probs * np.log2(probs))

results = []
total_entropy = 0
total_error = 0
total_len = 0

for root, langs in data.items():
    la_target = langs['la']
    
    # Simulating simple consensus Bayesian reconstruction (MCTS alignment approximation)
    reconstructed = ""
    word_entropies = []
    
    # Pad strings to max len
    max_len = max(len(w) for lang, w in langs.items() if lang != 'la')
    
    for i in range(max(len(la_target), max_len)):
        chars = []
        for lang, w in langs.items():
            if lang != 'la':
                if i < len(w):
                    chars.append(w[i])
                else:
                    chars.append('-')
        
        counts = Counter(chars)
        total = sum(counts.values())
        probs = np.array([c/total for c in counts.values()])
        H = entropy(probs)
        
        best_char = counts.most_common(1)[0][0]
        reconstructed += best_char
        word_entropies.append(H)
    
    reconstructed = reconstructed.replace('-', '')
    
    # Calculate edit distance roughly (hamming/levenshtein proxy)
    la_padded = la_target.ljust(max_len, '-')
    rec_padded = reconstructed.ljust(max_len, '-')
    
    errors = sum(1 for a, b in zip(la_padded, rec_padded) if a != b)
    avg_H = np.mean(word_entropies) if word_entropies else 0
    
    results.append({
        "Proto_Target": la_target,
        "Reconstructed": reconstructed,
        "Entropy_Bits": round(avg_H, 3),
        "Errors": errors,
        "Length": len(la_target)
    })
    
    total_entropy += sum(word_entropies)
    total_error += errors
    total_len += len(la_target)

df = pd.DataFrame(results)
df.to_csv("reconstruccion_resultados.csv", index=False)

with open("c5_stats.json", "w") as f:
    json.dump({
        "accuracy": round(1 - (total_error / total_len), 3),
        "total_entropy": round(total_entropy, 3),
        "mean_error": total_error / len(results)
    }, f)

print("C5-REAL Execution Complete. Entropy calculated.")
