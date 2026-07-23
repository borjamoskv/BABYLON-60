from collections import deque
from proof_kernel.crdt import CRDTMap
from proof_kernel.ast_rule import ASTRule

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
        raise ValueError("Ω159 Violated: Graph has cycles, topological sort failed.")
    return order

def dag_inference(initial_state: CRDTMap, dag: dict[str, list[str]], rules: dict[str, ASTRule], max_entropy: int = 1_000_000) -> tuple[CRDTMap, int]:
    """
    Ω159 · Dependency Closure & Ω166 · Pure Inference (CRDT)
    Ejecuta inferencia formal evaluando reglas AST en orden topológico estricto.
    Retorna el CRDT final y la entropía residual en microbits.
    """
    order = topological_sort(dag)
    node_states = {order[0]: initial_state}
    
    current_entropy = initial_state.measure_entropy(max_entropy)
    
    # Resolver en orden
    for node in order:
        current_state = node_states.get(node, CRDTMap())
        
        if node in rules:
            result_state = rules[node].execute(current_state)
            new_entropy = result_state.measure_entropy(max_entropy)
            # Asertar monotonicidad epistémica
            compute_information_gain(current_entropy, new_entropy)
            current_entropy = new_entropy
        else:
            result_state = current_state
            
        for child in dag.get(node, []):
            if child not in node_states:
                node_states[child] = result_state
            else:
                node_states[child] = node_states[child].merge(result_state)
                
    # Merge all sinks
    sinks = [n for n in dag if not dag.get(n)]
    if not sinks:
        sinks = [order[-1]]
        
    final_crdt = node_states[sinks[0]]
    for sink in sinks[1:]:
        final_crdt = final_crdt.merge(node_states[sink])
        
    final_entropy = final_crdt.measure_entropy(max_entropy)
    return final_crdt, final_entropy

def compute_information_gain(prior_microbits: int, posterior_microbits: int) -> int:
    """
    Ω162 · Falsification Power Invariant & Ω163 · Residual Entropy
    Para cumplir con INV_C5_18 (exclusión de flotantes BFT) sin destruir
    exergía matemática (truncamientos a 0), la Entropía de Shannon se 
    calcula y propaga en 'microbits' (1 bit = 1,000,000 microbits).
    """
    if prior_microbits < posterior_microbits:
        raise ValueError("Epistemic Monotonicity (Ω155) violated: entropy increased.")
    return prior_microbits - posterior_microbits
