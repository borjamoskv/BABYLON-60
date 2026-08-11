import numpy as np
import networkx as nx

np.random.seed(42)
N_SAMPLES = 200
N_GENES = 50
X_expr = np.random.normal(loc=5.0, scale=1.5, size=(N_SAMPLES, N_GENES))
latent_factor = np.random.normal(loc=10.0, scale=3.0, size=(N_SAMPLES,))
for i in range(5):
    X_expr[:, i] += latent_factor * 0.8 + np.random.normal(0, 0.5, N_SAMPLES)
R = np.corrcoef(X_expr, rowvar=False)
S = np.abs(R)
print("Max S:", np.max(S - np.eye(N_GENES)))
print("Mean S:", np.mean(S))
