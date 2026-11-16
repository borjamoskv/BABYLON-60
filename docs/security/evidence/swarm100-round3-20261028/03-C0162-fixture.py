"""C0162: cross-target conditional coherence, independent of pi0's time origin.

Only AST-selected mathematical functions and synthetic inputs are executed.
No product module, CLI, native gate, network, database or operator data is used.
"""

import ast
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import numpy as np


SOURCE = Path("tools/skill_library/global/categorical-hallucination-audit/scripts/audit_kl_d.py")
NAMES = {"compute_kan_extension_kl_d", "compute_wasserstein_1d", "audit_system"}
parsed = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
selected = [node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name in NAMES]
assert {node.name for node in selected} == NAMES
namespace = {"np": np}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(SOURCE), "exec"), namespace)

states = ["A", "B"]
transition = [[0.8, 0.2], [0.1, 0.9]]
history = {0: "A", 1: "B", 2: "B"}
window = [2]
targets = [0, 1]
given_prior = [1, 0]
audit_output = namespace["audit_system"](states, transition, given_prior, history, window, targets)
q0 = namespace["compute_kan_extension_kl_d"](states, transition, given_prior, history, window, 0)
q1 = namespace["compute_kan_extension_kl_d"](states, transition, given_prior, history, window, 1)
assert np.allclose(q0, [1, 0]) and np.allclose(q1, [1, 0])

# Any one Markov joint process with the supplied T must obey this identity:
# P(S1=j | S2=B) = sum_i P(S0=i | S2=B) * P(S1=j | S0=i,S2=B).
# The second factor is T[i,j]*T[j,B] / sum_k T[i,k]*T[k,B].
# This uses the function's own q0 posterior, not an assumed time origin for pi0.
t = [[Fraction(4, 5), Fraction(1, 5)], [Fraction(1, 10), Fraction(9, 10)]]
bridge = []
for i in range(2):
    weights = [t[i][j] * t[j][1] for j in range(2)]
    total = sum(weights)
    assert total > 0
    bridge.append([weight / total for weight in weights])
q0_exact = [Fraction(1), Fraction(0)]
required_q1 = [sum(q0_exact[i] * bridge[i][j] for i in range(2)) for j in range(2)]
assert required_q1 == [Fraction(8, 17), Fraction(9, 17)]
assert not np.allclose(q1, [float(x) for x in required_q1])

# A stationary prior is a positive control: the current formula can be correct
# when the same vector really is the marginal at all unobserved target times.
stationary = [Fraction(1, 3), Fraction(2, 3)]
assert [sum(stationary[i] * t[i][j] for i in range(2)) for j in range(2)] == stationary
stationary_float = [float(x) for x in stationary]
stationary_q0 = namespace["compute_kan_extension_kl_d"](states, transition, stationary_float, history, window, 0)
stationary_q1 = namespace["compute_kan_extension_kl_d"](states, transition, stationary_float, history, window, 1)
stationary_required_q1 = [sum(stationary_q0[i] * float(bridge[i][j]) for i in range(2)) for j in range(2)]
assert np.allclose(stationary_q1, stationary_required_q1)

print(json.dumps({
    "candidate_id": "SW100-C0162",
    "source_path": str(SOURCE),
    "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "scope": "Isolated exact-source mathematical functions; no product/native runtime or external effects.",
    "assumption": "One Markov process on the shared history with the provided transition matrix, as required by local MODULE.md:42-45. No assumption about pi0's time origin is needed for the bridge coherence test.",
    "inputs": {"states": states, "T": transition, "pi0": given_prior, "history": history, "window": window, "targets": targets},
    "actual_audit_output": audit_output,
    "actual_q0": q0.tolist(),
    "actual_q1": q1.tolist(),
    "required_q1_from_actual_q0": [str(x) for x in required_q1],
    "required_q1_float": [float(x) for x in required_q1],
    "bridge_rows": [[str(x) for x in row] for row in bridge],
    "conditional_coherence_violated": True,
    "stationary_prior_control": {"pi": [str(x) for x in stationary], "q0": stationary_q0.tolist(), "q1": stationary_q1.tolist(), "bridge_required_q1": stationary_required_q1, "coherent": True},
    "limit": "The primitive's undocumented pi0 time origin remains ambiguous. A single-target call can be correct if pi0 is that target's marginal. The reproduced defect is the public multi-target audit reusing one unrestricted vector as all target marginals under its single-process contract.",
}, indent=2))
