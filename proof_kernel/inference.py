from collections import deque
from proof_kernel.ast_rule import ASTRule
from proof_kernel.crdt import CRDTMap

def topological_sort(dag: dict[str, list[str]]) -> list[str]:
    in_degree = {u: 0 for u in dag}
    for u in dag:
        for v in dag[u]:
            in_degree.setdefault(v, 0)
            in_degree[v] += 1
    queue = deque([u for u in in_degree if in_degree[u] == 0])
    order = []
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in dag.get(u, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
    if len(order) != len(in_degree):
        raise ValueError('Ω159 Violated: Graph has cycles, topological sort failed.')
    return order

def dag_inference(initial_state: CRDTMap, dag: dict[str, list[str]], rules: dict[str, ASTRule], max_entropy: int=1000000) -> tuple[CRDTMap, int]:
    order = topological_sort(dag)
    node_states = {order[0]: initial_state}
    current_entropy = initial_state.measure_entropy(max_entropy)
    for node in order:
        current_state = node_states.get(node, CRDTMap())
        if node in rules:
            result_state = rules[node].execute(current_state)
            new_entropy = result_state.measure_entropy(max_entropy)
            compute_information_gain(current_entropy, new_entropy)
            current_entropy = new_entropy
        else:
            result_state = current_state
        for child in dag.get(node, []):
            if child not in node_states:
                node_states[child] = result_state
            else:
                node_states[child] = node_states[child].merge(result_state)
    sinks = [n for n in dag if not dag.get(n)]
    if not sinks:
        sinks = [order[-1]]
    final_crdt = node_states[sinks[0]]
    for sink in sinks[1:]:
        final_crdt = final_crdt.merge(node_states[sink])
    final_entropy = final_crdt.measure_entropy(max_entropy)
    return (final_crdt, final_entropy)

def compute_information_gain(prior_microbits: int, posterior_microbits: int) -> int:
    if prior_microbits < posterior_microbits:
        raise ValueError('Epistemic Monotonicity (Ω155) violated: entropy increased.')
    return prior_microbits - posterior_microbits